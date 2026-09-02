// Stripe donation checkout + webhook for Three Doors.
//
// Two HTTP functions:
//  - createCheckoutSession: the frontend POSTs { accountId, displayName },
//    gets back a Stripe Checkout URL for the $3/month subscription and
//    redirects the browser there.
//  - stripeWebhook: Stripe calls this on payment events. Donation totals
//    are only ever recorded from `invoice.paid` — that event fires for
//    every billing cycle (the first payment included), so recording from
//    both that and `checkout.session.completed` would double-count the
//    first payment.
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

exports.createCheckoutSession = onRequest(
  { secrets: [stripeSecretKey, stripePriceId] },
  async (req, res) => {
    setCors(res);
    if(req.method === "OPTIONS"){ res.status(204).send(""); return; }
    if(req.method !== "POST"){ res.status(405).json({ error: "Method not allowed" }); return; }

    const accountId = req.body && req.body.accountId;
    const displayName = (req.body && req.body.displayName || "").toString().slice(0, 100);
    if(!accountId || typeof accountId !== "string"){
      res.status(400).json({ error: "accountId required" });
      return;
    }

    try{
      const stripe = new Stripe(stripeSecretKey.value());
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
        metadata: { accountId, displayName }
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
        await recordDonation(event.data.object, stripe);
      }
      res.status(200).json({ received: true });
    }catch(err){
      console.error("Webhook handling failed", err);
      res.status(500).json({ error: "internal error" });
    }
  }
);

async function recordDonation(invoice, stripe){
  if(!invoice.subscription) return;

  const subscription = await stripe.subscriptions.retrieve(invoice.subscription);
  const meta = subscription.metadata || {};
  const accountId = meta.accountId;
  if(!accountId) return;

  const ref = db.doc("donations/" + accountId);
  await ref.set(
    {
      displayName: meta.displayName || accountId,
      totalCents: admin.firestore.FieldValue.increment(invoice.amount_paid || 0),
      currency: invoice.currency || "usd",
      lastDonatedAt: Date.now()
    },
    { merge: true }
  );
}
