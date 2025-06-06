from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class BM25Scorer:
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """Initialize BM25 scorer with parameters."""
        self.vectorizer = TfidfVectorizer()
        self.k1 = k1
        self.b = b

    def score(self, query: str, documents: List[str]) -> List[float]:
        """Calculate BM25 scores for documents against the query."""
        if not documents:
            return []

        try:
            # Convert documents to lowercase and remove special characters
            documents = [doc.lower() for doc in documents]
            query = query.lower()

            # Vectorize documents
            X = self.vectorizer.fit_transform(documents)
            query_vec = self.vectorizer.transform([query])

            # Get document lengths
            doc_lengths = np.array(X.sum(axis=1)).ravel()
            avg_doc_len = doc_lengths.mean()

            # Calculate BM25 scores
            scores = []
            for i in range(len(documents)):
                # Get term frequencies for this document
                tf = X[i, :].toarray()[0]
                
                # Calculate IDF for each term
                # Add small epsilon to avoid division by zero
                epsilon = 1e-10
                idf = np.log((len(documents) + epsilon) / 
                           (X[:, tf > 0].sum() + epsilon))
                
                # Calculate BM25 score for this document
                # Add small epsilon to avoid division by zero
                score = np.sum(idf * ((tf * (self.k1 + 1)) / 
                                    (tf + self.k1 * (1 - self.b + 
                                                     self.b * (doc_lengths[i] / (avg_doc_len + epsilon))))))
                scores.append(score)

            # Normalize scores to range [0, 1]
            scores = np.array(scores)
            if np.max(scores) > 0:
                scores = scores / np.max(scores)
            return scores.tolist()

        except Exception as e:
            logger.error(f"Error calculating BM25 scores: {e}")
            return [0.0] * len(documents)
