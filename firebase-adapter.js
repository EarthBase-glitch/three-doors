// Thin adapter that gives index.html / admin.html a small Firestore-flavored
// API (doc/collection/get/set/onSnapshot) so the app code doesn't need to
// know it's talking to Firebase directly.
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {
  getFirestore, doc, getDoc, setDoc, updateDoc, addDoc, deleteDoc,
  collection, query, where, orderBy, limit, getDocs, onSnapshot, increment
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";
import {
  getAuth, signInWithEmailAndPassword, onAuthStateChanged, signOut
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

const app = initializeApp(window.FIREBASE_CONFIG);
const firestore = getFirestore(app);
const auth = getAuth(app);

function wrapSnap(snap){
  return { id: snap.id, exists: snap.exists(), data: () => snap.data() };
}

function makeDocRef(path){
  const ref = doc(firestore, path);
  return {
    id: ref.id,
    path: ref.path,
    async get(){ return wrapSnap(await getDoc(ref)); },
    async set(data, options){ await setDoc(ref, data, options || {}); },
    async update(data){ await updateDoc(ref, data); },
    async delete(){ await deleteDoc(ref); },
    onSnapshot(next, err){
      return onSnapshot(ref, (snap) => next(wrapSnap(snap)), err);
    }
  };
}

function makeQueryLike(colPath, constraints){
  function build(){ return query(collection(firestore, colPath), ...constraints); }
  return {
    where(field, op, value){ return makeQueryLike(colPath, constraints.concat([where(field, op, value)])); },
    orderBy(field, dir){ return makeQueryLike(colPath, constraints.concat([orderBy(field, dir || "asc")])); },
    limit(n){ return makeQueryLike(colPath, constraints.concat([limit(n)])); },
    async get(){
      const snap = await getDocs(build());
      return { docs: snap.docs.map(wrapSnap) };
    },
    onSnapshot(next, err){
      return onSnapshot(build(), (snap) => next({ docs: snap.docs.map(wrapSnap) }), err);
    }
  };
}

function makeCollectionRef(path){
  const base = makeQueryLike(path, []);
  return Object.assign({}, base, {
    path,
    doc(id){
      const realId = id || doc(collection(firestore, path)).id;
      return makeDocRef(path + "/" + realId);
    },
    async add(data){
      const ref = await addDoc(collection(firestore, path), data);
      return makeDocRef(path + "/" + ref.id);
    }
  });
}

window.doorsDb = {
  doc: (p) => makeDocRef(p),
  collection: (p) => makeCollectionRef(p),
  // A Firestore FieldValue sentinel: pass the result inside a `set(data,
  // {merge:true})` call to atomically increment a field server-side —
  // safe even when many visitors write it at the same moment, and
  // creates the document (starting from the increment amount) if it
  // doesn't exist yet.
  increment: (n) => increment(n)
};

window.doorsAuth = {
  async signIn(email, password){
    const cred = await signInWithEmailAndPassword(auth, email, password);
    return cred.user;
  },
  signOut(){ return signOut(auth); },
  onChange(cb){ return onAuthStateChanged(auth, cb); },
  get currentUser(){ return auth.currentUser; }
};

window.dispatchEvent(new Event("doorsFirebaseReady"));
