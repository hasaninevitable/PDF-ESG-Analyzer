import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity



class SemanticSearchESG:
    def __init__(self, model_name='all-MiniLM-L6-v2', similarity_threshold=0.4):
        """
        Initialize the semantic search with embedding model and threshold.

        :param model_name: Name of the SentenceTransformer model.
        :param similarity_threshold: Cosine similarity threshold to filter results.
        """
        self.embedder = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold

        # Default ESG keywords set for query embedding
        self.esg_keywords = [
            "environment", "sustainability", "carbon footprint", "climate change",
            "social responsibility", "governance", "renewable energy", "emissions",
            "diversity", "ethical", "waste reduction", "greenhouse gas", "ESG"
        ]

        # Precompute embeddings for each keyword individually
        self.keyword_embeddings = self.embedder.encode(self.esg_keywords)

    def create_embeddings(self, extracted_chunks):
        """
        Generate embeddings for all extracted text chunks (usually sentences).

        :param extracted_chunks: List of dicts with extracted text and metadata.
        :return: List of embeddings array aligned to extracted_chunks list.
        """
        sentences = [chunk['text'] for chunk in extracted_chunks]
        embeddings = self.embedder.encode(sentences)
        return embeddings

    def run_semantic_search(self, extracted_chunks):
        """
        Runs semantic search over extracted text chunks to find ESG-related sentences.

        :param extracted_chunks: List of dicts with extracted text and metadata.
        :return: Filtered list of dicts with chunks passing similarity threshold,
                 each augmented with similarity score.
        """
        if not extracted_chunks:
            return []

        embeddings = self.create_embeddings(extracted_chunks)  # NxD embeddings

        results = []

        for idx, sentence_emb in enumerate(embeddings):
            # Compute similarities with all keyword embeddings
            sims = cosine_similarity(sentence_emb.reshape(1, -1), self.keyword_embeddings).flatten()
            max_sim = np.max(sims)

            if max_sim >= self.similarity_threshold:
                chunk = extracted_chunks[idx].copy()
                chunk['similarity'] = float(max_sim)
                results.append(chunk)

        return results
