import streamlit as st
import chromadb
from typing import cast
from chromadb.api.types import EmbeddingFunction, Documents
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pypdf import PdfReader

# d3 viz
import json
import streamlit.components.v1 as components
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

DB_PATH = "chroma_db"
COLLECTION_NAME = "rag_docs"

# chroma embedding function 
embedding_fn = cast(
    EmbeddingFunction[Documents],
    SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
)

# separate model for PCA viz
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# chromadb persistent client
client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn # type: ignore
)

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text
    
def chunk_text(text, chunk_size=700, overlap=100):
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        
    return chunks


def render_d3(plot_data):
    with open("index.html", "r") as f:
        html = f.read()

    with open("styles.css", "r") as f:
        css = f.read()

    with open("d3_viz.js", "r") as f:
        js = f.read()

    html = html.replace(
        '<link rel="stylesheet" href="styles.css">',
        f"<style>{css}</style>"
    )

    html = html.replace(
        '<script src="d3_viz.js"></script>',
        f"<script>{js}</script>"
    )

    html = html.replace("__DATA__", json.dumps(plot_data))

    components.html(html, height=620, scrolling=True)


uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    text = read_pdf(uploaded_file)
    chunks = chunk_text(text)
    
    ids = [f"{uploaded_file.name}_{i}" for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=[{"source": uploaded_file.name} for _ in chunks]
    )
    
    st.success("PDF added to vector database!")
    
query = st.text_input("Ask a question about your document")

if query:
    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    retrieved_docs = results["documents"][0] # type: ignore

    st.subheader("Top matching context")

    for doc in retrieved_docs:
        st.write(doc)
        st.divider()

    # ---- VECTOR VISUALIZATION ----
    st.subheader("Vector Space Visualization")

    # Combine docs + query
    all_texts = retrieved_docs + [query]

    embeddings = model.encode(all_texts)

    pca = PCA(n_components=2)
    points = pca.fit_transform(embeddings) # type: ignore

    plot_data = []

    for i, doc in enumerate(retrieved_docs):
        plot_data.append({
            "x": float(points[i][0]),
            "y": float(points[i][1]),
            "label": f"Chunk {i+1}",
            "text": doc[:300],
            "type": "chunk"
        })

    query_point = points[-1]

    plot_data.append({
        "x": float(query_point[0]),
        "y": float(query_point[1]),
        "label": "Query",
        "text": query,
        "type": "query"
    })

    # Render D3
    render_d3(plot_data)