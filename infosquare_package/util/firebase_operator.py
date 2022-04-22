import firebase_admin
from firebase_admin import credentials, firestore

from .encrypt import AESCipher


ENC_SNIPPET_PATH = "infosquare_package/resource/findfour/ttrjp-infosquare-firebase-adminsdk-aqv0i-b91de83940.json.enc"
snippet_path = ENC_SNIPPET_PATH.replace(".enc", "")

AESCipher().dectypt_file(
    enc_filepath=ENC_SNIPPET_PATH,
    dec_filepath=snippet_path
)

cred = credentials.Certificate(snippet_path)
firebase_admin.initialize_app(cred)
db = firestore.client()


def set_doc(collection_name: str, doc_dict: dict) -> None:
    docs = db.collection(collection_name).document()
    docs.set(doc_dict)


def get_doc_list(collection_name: str) -> list[dict]:
    return [doc.to_dict() for doc in db.collection(collection_name).get()]
