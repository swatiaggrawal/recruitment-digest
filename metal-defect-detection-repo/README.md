# Metal Surface Defect Detection
### Computer Vision — MSc Computer Science, Sapienza University of Rome

> **Authors:** Swati Aggrawal & Vibha Sengar  
> **Course:** Computer Vision  
> **Program:** M.Sc. Computer Science — Sapienza University of Rome  
> **Date:** January 2025

---

## Overview

This project addresses automated defect detection on metal surfaces — a core challenge in industrial quality control and a key capability for next-generation intelligent manufacturing systems. We benchmark three machine learning approaches on the **NEU Metal Surface Defects Dataset**, comparing deep learning (CNN) against classical computer vision pipelines (SVM with HOG features, Random Forest with HOG features) across six defect categories.

The work demonstrates the full pipeline from raw image ingestion and augmentation to model training, hyperparameter search, evaluation, and visual analysis — skills directly applicable to industrial inspection, autonomous operation, and visual asset analysis in energy and manufacturing domains.

---

## Problem Statement

Metal surfaces can develop six distinct defect types during production. Manual inspection is slow, subjective, and unscalable. This project builds and compares automated classifiers that can identify defect type from grayscale surface images, enabling real-time quality assurance on production lines.

---

## Dataset

**NEU Metal Surface Defects Dataset** (Kaggle: `fantacher/neu-metal-surface-defects-data`)

| Split | Images |
|-------|--------|
| Train | 1,654  |
| Validation | 72 |
| Test  | 72     |

**6 defect classes:** Crazing, Inclusion, Patches, Pitted Surface, Rolled-in Scale, Scratches

---

## Methods

### 1. Convolutional Neural Network (CNN)
A custom CNN built with TensorFlow/Keras:

| Layer | Output Shape | Parameters |
|-------|-------------|------------|
| Conv2D (32 filters, 3×3) + ReLU | 198×198×32 | 896 |
| MaxPooling2D | 99×99×32 | 0 |
| Conv2D (64 filters, 3×3) + ReLU | 97×97×64 | 18,496 |
| MaxPooling2D | 48×48×64 | 0 |
| Conv2D (128 filters, 3×3) + ReLU | 46×46×128 | 73,856 |
| MaxPooling2D | 23×23×128 | 0 |
| Flatten | 67,712 | 0 |
| Dense (256) + Dropout | 256 | 17,334,528 |
| Dense (6, softmax) | 6 | 1,542 |
| **Total** | | **~17.4M params** |

**Training details:**
- Optimizer: Adam, Loss: Categorical Cross-Entropy
- Data augmentation: shear (0.2), horizontal flip, rescaling (1/255)
- Callbacks: ModelCheckpoint, EarlyStopping (patience=10), ReduceLROnPlateau

### 2. SVM with HOG Features
- Feature extraction: **Histogram of Oriented Gradients (HOG)** via `skimage.feature`
- Classifier: **SVC** with RBF kernel (`C=10`, `gamma='scale'`)
- Training on combined train + validation sets

### 3. Random Forest with HOG Features
- Same HOG feature pipeline as SVM
- `RandomForestClassifier` with hyperparameter tuning via `GridSearchCV`

---

## Repository Structure

```
metal-defect-detection/
│
├── CVproject.ipynb          # Main notebook — full pipeline
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

---

## Setup & Usage

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/metal-defect-detection.git
cd metal-defect-detection
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download the dataset
You need a Kaggle API key (`kaggle.json`) placed in your Google Drive or local `~/.kaggle/` directory.

```bash
kaggle datasets download -d fantacher/neu-metal-surface-defects-data
unzip neu-metal-surface-defects-data.zip -d data/
```

### 4. Run the notebook
Open `CVproject.ipynb` in Jupyter or Google Colab and update the dataset path variables at the top of Section 2:

```python
train_dir = 'data/NEU Metal Surface Defects Data/train'
test_dir  = 'data/NEU Metal Surface Defects Data/test'
valid_dir = 'data/NEU Metal Surface Defects Data/valid'
```

---

## Key Results

| Model | Test Accuracy |
|-------|--------------|
| CNN   | See notebook |
| SVM (HOG + RBF kernel) | See notebook |
| Random Forest (HOG + GridSearch) | See notebook |

Evaluation metrics include accuracy, precision, recall, F1-score, and confusion matrices for all three models. t-SNE and PCA visualizations are provided for feature space analysis.

---

## Technologies

| Category | Tools |
|----------|-------|
| Deep Learning | TensorFlow / Keras |
| Classical ML | scikit-learn (SVM, RandomForest, GridSearchCV) |
| Feature Engineering | scikit-image (HOG) |
| Dimensionality Reduction | PCA, t-SNE |
| Visualization | Matplotlib, Seaborn |
| Data | NumPy, Pandas, PIL |
| Platform | Google Colab (T4 GPU) |

---

## Relevance to Industrial Applications

This project aligns directly with real-world needs in automated industrial inspection:

- **Defect detection** — classifying surface anomalies mirrors inspection tasks in energy infrastructure, turbine components, and manufacturing QA
- **Feature extraction pipeline** — HOG-based features are lightweight and interpretable, suitable for edge deployment
- **Deep learning vs. classical trade-off** — the comparison informs architectural decisions for resource-constrained vs. accuracy-critical deployment scenarios
- **Scalable methodology** — the pipeline generalizes to other visual asset analysis tasks (corrosion, fatigue cracks, weld quality)

---

## Authors

**Swati Aggrawal** — M.Sc. Computer Science, Sapienza University of Rome  
**Vibha Sengar** — M.Sc. Computer Science, Sapienza University of Rome

---

## License

This project was developed for academic purposes as part of the Computer Vision course at Sapienza University of Rome. The NEU Metal Surface Defects Dataset is subject to its own license (see [Kaggle dataset page](https://www.kaggle.com/datasets/fantacher/neu-metal-surface-defects-data)).
