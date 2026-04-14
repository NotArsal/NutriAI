# Research Paper Draft — NutriPlanner

## Target Venue: IEEE EMBC 2026 (4-page short paper)
**Conference**: 48th Annual International Conference of the IEEE Engineering in Medicine and Biology Society  
**Typical deadline**: January 2026  
**Format**: 4-page IEEE conference paper  

---

## Draft Abstract

**NutriPlanner: An Explainable Machine Learning System for Personalised Clinical Nutrition Recommendations with Uncertainty Quantification**

*Abstract* — Clinical nutrition management for patients with metabolic diseases (diabetes, hypertension, obesity) remains challenging due to the heterogeneity of patient biomarker profiles, dietary preferences, and adherence patterns. We present **NutriPlanner**, a full-stack clinical decision support system that combines gradient boosting and random forest models to deliver personalised diet protocol recommendations, meal planning, and health risk scoring from a compact 18-feature biomarker profile. The system incorporates three novel contributions: (1) SHAP (SHapley Additive exPlanations) TreeExplainer-based feature attribution that surfaces the top-*k* clinical drivers of each prediction in human-readable form, enabling physician interpretability; (2) 90% confidence intervals on the continuous risk score derived from per-tree prediction variance of the Random Forest ensemble, implementing the Meinshausen (2006) Quantile Regression Forest approach; and (3) a layered FastAPI microservice architecture with structured JSON logging, per-IP rate limiting, and a HuggingFace-compatible model card that encodes training data provenance, known limitations, and bias analysis. Preliminary evaluation on 1,000 synthetic patient records yields diet classification cross-validation accuracy of 0.97 (post-regularisation) and risk score RMSE of 3.93 (scale 0–100). The system is deployed as a React/Vite progressive web application with an AI consultation module. Future work targets training data replacement with NHANES 2017–2018 (~40,000 records) and the addition of a federated learning layer for privacy-preserving multi-site deployment. All code and model cards are open-source.

*Index Terms* — clinical decision support, explainable AI, SHAP, random forests, gradient boosting, nutrition informatics, digital health, uncertainty quantification

---

## Key Contributions (for reviewer's checklist)

1. **Explainability layer**: SHAP TreeExplainer applied to clinical nutrition — first deployment in a full-stack patient-facing application with per-prediction explanation API
2. **Uncertainty quantification**: 90% CI on risk score from RF tree variance — gives clinicians a signal range rather than a point estimate
3. **Open model card**: HuggingFace-style model card with bias analysis for a nutrition recommendation system
4. **System architecture**: Layer-separated FastAPI backend with rate limiting, JSON logging, and lifespan-managed model loading — a reference architecture for clinical ML deployment

---

## Suggested Title Variants

1. NutriPlanner: Explainable Clinical Nutrition Recommendations with Uncertainty-Aware Risk Scoring
2. An Interpretable Machine Learning Pipeline for Personalised Dietary Guidance in Metabolic Disease Management
3. SHAP-Augmented Diet Protocol Recommendation with Confidence-Bounded Risk Assessment: A Full-Stack Clinical AI System

---

## Recommended Reviewers & Related Work to Cite

- Kavakiotis et al. (2017), *Computational and Structural Biotechnology Journal* — ML in diabetes
- Lundberg & Lee (2017), *NeurIPS* — SHAP
- Meinshausen (2006), *JMLR* — Quantile RF (CI implementation reference)
- Papagiannidis et al. (2023), *Clinical Nutrition ESPEN* — ML in clinical nutrition systematic review

---

## Novel Contribution Ideas to Elevate to Full Paper

### Option A: LLM-Augmented Clinical Reasoning Layer
Add a GPT-4/Gemini API call after ML inference that generates a 3-sentence clinical rationale personalised to the patient's SHAP explanation:
> "Your highest-risk biomarker is glucose (SHAP contribution: +8.4), consistent with your Diabetes diagnosis. The Low-Carb protocol is recommended with 94% confidence to address this. Your physical activity level reduces your risk by 3.1 points — maintain your current exercise routine."

**Publishability**: Novel application of LLM+ML hybrid for clinical explainability — suitable for **ACM CHIL 2026**.

### Option B: Federated Learning for Privacy-Preserving Multi-Site Training
Use **Flower (flwr)** framework to train across simulated hospital nodes without sharing raw data:
```python
import flwr as fl

class NutriPlannerClient(fl.client.NumPyClient):
    def fit(self, parameters, config):
        # Local training on hospital-specific data
        ...
```
**Publishability**: Novel federated approach to diet recommendation — suitable for **NeurIPS FedML Workshop 2026**.

### Option C: Multi-Modal Input (Food Photo + Biomarkers)
Combine CLIP image embeddings from food photos with biomarker features:
```python
from transformers import CLIPModel, CLIPProcessor
clip = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# food_embedding = clip.get_image_features(pixel_values=food_photo)
# combined = torch.cat([food_embedding, biomarker_tensor], dim=1)
```
**Publishability**: Multi-modal clinical nutrition — suitable for **IEEE BIBM 2026**.

---

## Paper Structure (IEEE 4-page format)

```
I.   INTRODUCTION (0.5 pages)
     - Clinical nutrition challenge
     - Gap: lack of explainable, uncertainty-aware systems
     - Contributions

II.  SYSTEM ARCHITECTURE (1 page)
     - Input feature schema (18 features, Table 1)
     - 3-model ensemble diagram
     - SHAP integration
     - CI computation

III. METHODOLOGY (0.75 pages)
     - GBM for diet classification (Chen & Guestrin 2016)
     - RF for risk regression (Breiman 2001)
     - SHAP TreeExplainer (Lundberg & Lee 2017)
     - Meinshausen CI (2006)

IV.  RESULTS (0.75 pages)
     - Table 2: Model performance metrics
     - Figure 1: SHAP beeswarm plot for top features
     - Figure 2: CI range distribution across patient cohorts

V.   DISCUSSION & LIMITATIONS (0.5 pages)
     - Synthetic data — upgrade to NHANES
     - Binary gender limitation

VI.  CONCLUSION & FUTURE WORK (0.25 pages)
     - NHANES retraining
     - Federated learning
     - Streaming LLM consultation

REFERENCES
```
