import joblib
import numpy as np
import shap
from lime.lime_text import LimeTextExplainer

class XAIService:
    def __init__(self, model=None, vectorizer=None, model_path='linear_svm_model.pkl',
                 vectorizer_path='tfidf_vectorizer.pkl', clean_label='ham', label_encoder=None):
        # Accept already-loaded model/vectorizer (e.g. from api.py) to avoid loading
        # the pickles twice and to sidestep relative-path issues tied to the
        # process's current working directory.
        self.model = model if model is not None else joblib.load(model_path)
        self.vectorizer = vectorizer if vectorizer is not None else joblib.load(vectorizer_path)
        self.label_encoder = label_encoder
        self.clean_label = clean_label

        class_names = list(label_encoder.classes_) if label_encoder is not None else ['Ham', 'Spam']
        self.explainer = LimeTextExplainer(class_names=class_names)

        # Background samples for SHAP
        self.background_texts = ["free lottery", "hello friend", "urgent meeting", "win cash"]
        self.background_features = self.vectorizer.transform(self.background_texts)

    def _predict_proba_wrapper(self, texts):
        features = self.vectorizer.transform(texts)
        decision = self.model.decision_function(features)
        if decision.ndim > 1:
            decision = decision[:, 1]
        probs = 1 / (1 + np.exp(-decision))
        n_samples = len(texts)
        prob_matrix = np.zeros((n_samples, 2))
        prob_matrix[:, 1] = probs
        prob_matrix[:, 0] = 1 - probs
        return prob_matrix

    def get_local_explanation(self, text):
        exp = self.explainer.explain_instance(text, self._predict_proba_wrapper, num_features=5)
        return [[str(word), float(score)] for word, score in exp.as_list()]

    def get_global_importance(self):
        """Generates global feature importance using SHAP for the spam classifier.

        Averages |SHAP value| across every non-clean class (e.g. "spam" and
        "smishing"), not just one of them, so words that drive either verdict
        show up as indicators.
        """
        # 1. Convert to dense array
        dense_background = self.background_features.toarray()

        # 2. Initialize and calculate
        explainer = shap.LinearExplainer(self.model, dense_background)
        shap_values = explainer.shap_values(dense_background)

        # 3. Resolve which class index is the "clean" verdict (e.g. "ham") so we
        # can average importance over every other class instead of assuming a
        # fixed index. Falls back to index 1 for plain binary models.
        if isinstance(shap_values, list):
            shap_values = np.stack(shap_values, axis=-1)

        if shap_values.ndim == 3:
            clean_index = 0
            if self.label_encoder is not None:
                classes = list(self.label_encoder.classes_)
                if self.clean_label in classes:
                    clean_index = classes.index(self.clean_label)
            non_clean_indices = [i for i in range(shap_values.shape[-1]) if i != clean_index]
            shap_values = shap_values[:, :, non_clean_indices].mean(axis=-1)

        # 4. Calculate mean absolute importance
        feature_names = self.vectorizer.get_feature_names_out()
        importance = np.abs(shap_values).mean(axis=0)

        # 5. Pair and sort
        feature_importance = dict(zip(feature_names, importance))
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

        return [[word, float(score)] for word, score in sorted_importance]
