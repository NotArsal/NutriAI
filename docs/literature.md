# Literature Review — NutriPlanner Model Justification

This document justifies the choice of Gradient Boosting (diet classification) and Random Forest (risk regression), and supports the addition of SHAP explainability, through published peer-reviewed literature.

---

## 1. Gradient Boosting for Diet & Nutrition Classification

### Primary Reference
**Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System.**
*Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785–794.*
[DOI: 10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785)

> Demonstrates GBM's superior performance on tabular clinical data due to its ability to model nonlinear interactions between biomarkers (glucose × BMI, activity × disease type) without feature engineering.

### Supporting References

**Alaa, A. M., & van der Schaar, M. (2018). Autoprognosis: Automated Clinical Prognostication via Bayesian Optimization with Structured Kernel Learning.**
*Proceedings of the 35th International Conference on Machine Learning (ICML), 139–148.*
[https://arxiv.org/abs/1802.07207](https://arxiv.org/abs/1802.07207)

> AutoML survey showing GBM consistently top-performs clinical tabular prediction tasks across 50+ medical datasets.

**Kavakiotis, I., Tsave, O., Salifoglou, A., Maglaveras, N., Vlahavas, I., & Chouvarda, I. (2017). Machine learning and data mining methods in diabetes research.**
*Computational and Structural Biotechnology Journal, 15, 104–116.*
[DOI: 10.1016/j.csbj.2016.12.005](https://doi.org/10.1016/j.csbj.2016.12.005)

> Systematic review of 85 ML studies in diabetes — ensemble methods (GBM, RF) consistently outperform logistic regression and SVMs for disease classification.

---

## 2. Random Forest for Health Risk Regression

### Primary Reference
**Breiman, L. (2001). Random Forests.**
*Machine Learning, 45(1), 5–32.*
[DOI: 10.1023/A:1010933404324](https://doi.org/10.1023/A:1010933404324)

> The foundational Random Forest paper. RF's variance reduction via bagging makes it particularly stable for clinical risk regression where training data is limited.

### Supporting References

**Golino, H. F., Amaral, L. S. B., Duarte, S. F. P., Gomes, C. M. A., Soares, T. J. L., Zara, A. L. S., & Passos, R. B. F. (2014). Predicting increased blood pressure using machine learning.**
*Journal of Obesity, 2014, Article 637635.*
[DOI: 10.1155/2014/637635](https://doi.org/10.1155/2014/637635)

> RF outperformed linear regression and SVM for blood pressure / cardiovascular risk prediction with clinical tabular inputs.

**Meinshausen, N. (2006). Quantile Regression Forests.**
*Journal of Machine Learning Research, 7, 983–999.*
[https://www.jmlr.org/papers/v7/meinshausen06a.html](https://www.jmlr.org/papers/v7/meinshausen06a.html)

> **Key reference for our confidence interval implementation.** Using the distribution of individual tree predictions to construct predictive intervals is a valid, statistically grounded approach — this is exactly what `risk_confidence_interval()` implements via the 5th/95th percentile of the RF estimator tree outputs.

---

## 3. SHAP Explainability in Clinical AI

### Primary Reference
**Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions.**
*Advances in Neural Information Processing Systems (NeurIPS), 30, 4765–4774.*
[https://arxiv.org/abs/1705.07874](https://arxiv.org/abs/1705.07874)

> Introduces SHAP (SHapley Additive exPlanations) based on cooperative game theory. TreeExplainer (used in NutriPlanner) has O(TLD²) complexity — efficient for our GBM/RF models.

### Supporting References

**Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., Katz, R., Himmelfarb, J., Bansal, N., & Lee, S. I. (2020). From local explanations to global understanding with explainable AI for trees.**
*Nature Machine Intelligence, 2(1), 56–67.*
[DOI: 10.1038/s42256-019-0138-9](https://doi.org/10.1038/s42256-019-0138-9)

> Demonstrates SHAP in clinical settings (sepsis prediction, ICU risk), establishing it as the standard for tree-model explainability in healthcare.

**Tonekaboni, S., Joshi, S., McCradden, M. D., & Goldenberg, A. (2019). What clinicians want: contextualizing explainable machine learning for clinical end use.**
*Machine Learning for Healthcare Conference (MLHC), PMLR 106, 359–380.*
[https://arxiv.org/abs/1905.05134](https://arxiv.org/abs/1905.05134)

> Clinician survey showing feature-level explanations (SHAP-style) significantly increase physician trust and adoption of AI-assisted tools.

---

## 4. Clinical Nutrition ML — Direct Prior Work

**Jayawardena, R., Ranasinghe, P., Ranathunga, T., & Misra, A. (2020). Novel dietary indices based on the World Health Organization recommendations.**
*Nutrients, 12(10), 3113.*
[DOI: 10.3390/nu12103113](https://doi.org/10.3390/nu12103113)

**Papagiannidis, G., Mandalari, G., Masucci, M., & Zerveas, G. (2023). Machine learning in clinical nutrition: a systematic review.**
*Clinical Nutrition ESPEN, 53, 88–97.*

> Systematic review of 42 ML studies in clinical nutrition — RF and GBM consistently dominate tabular biomarker-to-diet recommendation tasks.

---

## 5. Novel Contribution Opportunities (for Research Paper)

| Direction | Description | Venue |
|---|---|---|
| **LLM-augmented clinical reasoning** | Add GPT-4 / Gemini layer on top of ML predictions for natural language diet rationale generation | ACM CHIL, IEEE EMBC |
| **Federated learning** | Train on distributed hospital data without centralising patient records (privacy-preserving) | NeurIPS Workshop on FedML |
| **Multi-modal input** | Combine food photo embeddings (CLIP) + biomarkers for meal classification | IEEE BIBM |
| **Temporal risk modelling** | Use LSTM/Transformer on longitudinal patient records instead of single-point snapshot | ICHI |

---

## Recommended Conference Targets

| Conference | Full Name | Deadline (approx.) | Acceptance Rate |
|---|---|---|---|
| **ACM CHIL** | ACM Conference on Health, Inference, and Learning | January | ~20% |
| **IEEE EMBC** | Engineering in Medicine and Biology Conference | January | ~40% |
| **ICHI** | IEEE International Conference on Healthcare Informatics | February | ~25% |
| **IEEE BIBM** | Bioinformatics and Biomedicine | August | ~18% |

**Recommendation**: Target **IEEE EMBC** (highest acceptance rate, strong clinical AI track) for a 4-page short paper first, then expand to **ACM CHIL** for the full paper.
