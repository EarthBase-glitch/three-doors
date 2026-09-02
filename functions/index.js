// Stripe donation checkout + webhook for Three Doors.
//
// Two HTTP functions:
//  - createCheckoutSession: the frontend POSTs { accountId, displayName,
//    kind, amountCents }. kind "subscribe" (default) starts the $3/month
//    subscription; kind "tip" starts a one-time payment for amountCents
//    (no account required to keep paying afterward). Either way the
//    response is a Stripe Checkout URL to redirect the browser to.
//  - stripeWebhook: Stripe calls this on payment events.
//     - `invoice.paid` records subscription donations — it fires for
//       every billing cycle (the first payment included), so recording
//       from both that and `checkout.session.completed` would
//       double-count a subscription's first payment.
//     - `checkout.session.completed` records tips, but only when
//       session.mode is "payment" (one-time) — a subscription checkout's
//       completion is intentionally ignored here since invoice.paid
//       already covers it.
//
// Secrets (never in code): set via `firebase functions:secrets:set NAME`.
//  - STRIPE_SECRET_KEY    Stripe secret API key (sk_test_... / sk_live_...)
//  - STRIPE_WEBHOOK_SECRET  signing secret for the webhook endpoint (whsec_...)
//  - STRIPE_PRICE_ID      the recurring Price ID for the $3/month donation

const { onRequest } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");
const Stripe = require("stripe");

admin.initializeApp();
const db = admin.firestore();

const stripeSecretKey = defineSecret("STRIPE_SECRET_KEY");
const stripeWebhookSecret = defineSecret("STRIPE_WEBHOOK_SECRET");
const stripePriceId = defineSecret("STRIPE_PRICE_ID");

const ALLOWED_ORIGIN = "https://earthbase-glitch.github.io";
const SUCCESS_URL = "https://earthbase-glitch.github.io/three-doors/?donated=1";
const CANCEL_URL = "https://earthbase-glitch.github.io/three-doors/?donated=0";

function setCors(res){
  res.set("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
  res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type");
}

const MIN_TIP_CENTS = 100;
const MAX_TIP_CENTS = 50000;

exports.createCheckoutSession = onRequest(
  { secrets: [stripeSecretKey, stripePriceId] },
  async (req, res) => {
    setCors(res);
    if(req.method === "OPTIONS"){ res.status(204).send(""); return; }
    if(req.method !== "POST"){ res.status(405).json({ error: "Method not allowed" }); return; }

    const accountId = req.body && req.body.accountId;
    const displayName = (req.body && req.body.displayName || "").toString().slice(0, 100);
    const kind = (req.body && req.body.kind) === "tip" ? "tip" : "subscribe";
    if(!accountId || typeof accountId !== "string"){
      res.status(400).json({ error: "accountId required" });
      return;
    }

    try{
      const stripe = new Stripe(stripeSecretKey.value());

      if(kind === "tip"){
        const amountCents = Math.round(Number(req.body && req.body.amountCents));
        if(!Number.isInteger(amountCents) || amountCents < MIN_TIP_CENTS || amountCents > MAX_TIP_CENTS){
          res.status(400).json({ error: "amountCents must be between " + MIN_TIP_CENTS + " and " + MAX_TIP_CENTS });
          return;
        }
        const session = await stripe.checkout.sessions.create({
          mode: "payment",
          line_items: [{
            price_data: {
              currency: "usd",
              unit_amount: amountCents,
              product_data: { name: "Three Doors — one-time tip" }
            },
            quantity: 1
          }],
          success_url: SUCCESS_URL,
          cancel_url: CANCEL_URL,
          client_reference_id: accountId,
          metadata: { accountId, displayName, kind: "tip" }
        });
        res.status(200).json({ url: session.url });
        return;
      }

      const session = await stripe.checkout.sessions.create({
        mode: "subscription",
        line_items: [{ price: stripePriceId.value(), quantity: 1 }],
        success_url: SUCCESS_URL,
        cancel_url: CANCEL_URL,
        client_reference_id: accountId,
        // Metadata on the Checkout Session does NOT automatically carry
        // over to the Subscription it creates — set it explicitly here so
        // every future invoice (renewals included) can still be traced
        // back to this account.
        subscription_data: {
          metadata: { accountId, displayName }
        },
        metadata: { accountId, displayName, kind: "subscribe" }
      });
      res.status(200).json({ url: session.url });
    }catch(err){
      console.error("createCheckoutSession failed", err);
      res.status(500).json({ error: "Could not start checkout" });
    }
  }
);

exports.stripeWebhook = onRequest(
  { secrets: [stripeSecretKey, stripeWebhookSecret] },
  async (req, res) => {
    const stripe = new Stripe(stripeSecretKey.value());
    const sig = req.headers["stripe-signature"];
    let event;
    try{
      event = stripe.webhooks.constructEvent(req.rawBody, sig, stripeWebhookSecret.value());
    }catch(err){
      console.error("Webhook signature verification failed", err.message);
      res.status(400).send("Webhook signature verification failed");
      return;
    }

    try{
      if(event.type === "invoice.paid"){
        await recordSubscriptionPayment(event.data.object, stripe);
      }else if(event.type === "checkout.session.completed"){
        await recordTipPayment(event.data.object);
      }
      res.status(200).json({ received: true });
    }catch(err){
      console.error("Webhook handling failed", err);
      res.status(500).json({ error: "internal error" });
    }
  }
);

async function recordSubscriptionPayment(invoice, stripe){
  if(!invoice.subscription) return;

  const subscription = await stripe.subscriptions.retrieve(invoice.subscription);
  const meta = subscription.metadata || {};
  const accountId = meta.accountId;
  if(!accountId) return;

  await addToDonationTotal(accountId, meta.displayName, invoice.amount_paid, invoice.currency);
}

async function recordTipPayment(session){
  // Subscription checkouts also fire checkout.session.completed —
  // invoice.paid already records those, so only one-time payments here.
  if(session.mode !== "payment") return;

  const meta = session.metadata || {};
  const accountId = meta.accountId;
  if(!accountId) return;

  await addToDonationTotal(accountId, meta.displayName, session.amount_total, session.currency);
}

async function addToDonationTotal(accountId, displayName, amountCents, currency){
  const ref = db.doc("donations/" + accountId);
  await ref.set(
    {
      displayName: displayName || accountId,
      totalCents: admin.firestore.FieldValue.increment(amountCents || 0),
      currency: currency || "usd",
      lastDonatedAt: Date.now()
    },
    { merge: true }
  );
}
