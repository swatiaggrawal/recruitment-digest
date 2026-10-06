# Metal Surface Defect Detection

Classifying six types of steel surface defects from images, and comparing a **CNN** against two classical machine learning models (**SVM** and **Random Forest**) that use **HOG** features.

Computer Vision course project, M.Sc. Computer Science, Sapienza University of Rome (January 2025).
Authors: Swati Aggrawal and Vibha Sengar.

---

## Results at a glance

| Model | Input | Test accuracy | Correct / 72 |
|-------|-------|:-------------:|:------------:|
| **CNN (3 conv blocks)** | raw pixels, 200x200 | **95.83%** | 69 |
| SVM (RBF kernel, C=10) | HOG features | 86.11% | 62 |
| Random Forest (200 trees, max depth 20) | HOG features | 62.50% | 45 |

The CNN beats the SVM by about 10 percentage points and the Random Forest by about 33. The classical models see only a fixed HOG description of each image, while the CNN learns its own features directly from the pixels.

Weighted precision, recall and F1 on the test set:

| Model | Precision | Recall | F1 |
|-------|:---------:|:------:|:--:|
| CNN | 0.967 | 0.958 | 0.958 |
| SVM | 0.879 | 0.861 | 0.850 |
| Random Forest | 0.625 | 0.625 | 0.596 |

---

## The problem

Steel surfaces can develop different defects during production. Checking them by eye is slow and inconsistent, so this project builds classifiers that look at an image and name the defect type.

## The data

**NEU Metal Surface Defects** dataset ([Kaggle: fantacher/neu-metal-surface-defects-data](https://www.kaggle.com/datasets/fantacher/neu-metal-surface-defects-data)).

| Split | Images | Used for |
|-------|:------:|----------|
| Train | 1,654 | training |
| Validation | 72 | CNN: early stopping and model selection. SVM and Random Forest: merged into training, tuned with cross-validation |
| Test | 72 | final score, used once per model |

There are 6 classes: **Crazing, Inclusion, Patches, Pitted, Rolled (rolled-in scale), Scratches**. The test set has exactly 12 images per class.

---

## The three models

### 1. CNN

A small convolutional network built with TensorFlow/Keras. Each block finds patterns (convolution), keeps the strongest responses (max pooling), and halves the image size.

| Layer | Output shape | Parameters |
|-------|-------------|-----------:|
| Conv2D, 32 filters 3x3, ReLU | 198 x 198 x 32 | 896 |
| MaxPooling 2x2 | 99 x 99 x 32 | 0 |
| Conv2D, 64 filters 3x3, ReLU | 97 x 97 x 64 | 18,496 |
| MaxPooling 2x2 | 48 x 48 x 64 | 0 |
| Conv2D, 128 filters 3x3, ReLU | 46 x 46 x 128 | 73,856 |
| MaxPooling 2x2 | 23 x 23 x 128 | 0 |
| Flatten | 67,712 | 0 |
| Dense 256, ReLU, Dropout 0.5 | 256 | 17,334,528 |
| Dense 6, softmax | 6 | 1,542 |
| **Total** | | **17,429,318** |

Almost all parameters sit in the first Dense layer, which is why Dropout is placed right after it.

**Training setup**
- Optimizer Adam, loss categorical cross-entropy, up to 25 epochs, batch size 36.
- Augmentation on training images only: shear (0.2) and horizontal flip. All images are rescaled to the range 0 to 1. Validation and test images get no augmentation.
- Three callbacks, all watching **validation loss**:
  - `ModelCheckpoint` saves the best model so far.
  - `ReduceLROnPlateau` multiplies the learning rate by 0.2 after 5 epochs without improvement. In the final run it dropped from 0.001 to 0.0002 after epoch 11 and to 0.0001 after epoch 19.
  - `EarlyStopping` (patience 10) restores the best weights. In the final run training ran all 25 epochs and the best epoch was the last one (validation loss 0.0295).
- Test result: **95.83% accuracy (69 of 72), test loss 0.114.**

### 2. SVM with HOG features

- **HOG (Histogram of Oriented Gradients)** from `scikit-image` turns each image into a vector describing the directions of edges in small regions. It is a fixed, hand-designed description and nothing is learned.
- Classifier: `SVC` with an RBF kernel.
- Tuning: `GridSearchCV`, 3-fold cross-validation on train plus validation, over `C` in {10, 100} with `gamma='scale'`. Both values of C gave the same cross-validation score (82.4% mean), and C=10 was kept.
- Test result: **86.11% (62 of 72).**

### 3. Random Forest with HOG features

- Same HOG features as the SVM.
- Tuning: `GridSearchCV`, 3-fold cross-validation on train plus validation, over `max_depth` in {20, None}, with 200 trees, `min_samples_leaf=2` and `max_features='sqrt'`. Best: `max_depth=20` (68.1% mean cross-validation score).
- Test result: **62.50% (45 of 72).**

---

## Where the models go wrong

The confusion matrices on the test set show which classes get mixed up.

- **CNN:** all 3 mistakes are the same one: Pitted images predicted as Inclusion. Every other class is perfect (12 of 12).
- **SVM:** 10 mistakes, all in two classes. Pitted (6 of 12 correct) is confused with Inclusion, Scratches and Crazing. Scratches (8 of 12 correct) is confused mostly with Patches.
- **Random Forest:** 27 mistakes, spread widely. Patches (3 of 12 correct), Pitted (4 of 12) and Scratches (5 of 12) are the weakest. Only Crazing and Rolled are perfect.

Pitted and Inclusion are both small dark spots on the surface, and Scratches and Patches are both elongated texture regions, so these pairs look alike. The notebook shows side-by-side example images of both pairs.

## How reliable are these numbers?

The test set has only 72 images, so **one image is about 1.4 percentage points**. The 95% confidence intervals (Wilson method) show how much the scores could move on a different test sample:

| Model | Accuracy | 95% interval |
|-------|:--------:|:------------:|
| CNN | 95.8% | 88.5% to 98.6% |
| SVM | 86.1% | 76.3% to 92.3% |
| Random Forest | 62.5% | 51.0% to 72.8% |

The CNN is clearly better than the Random Forest. Against the SVM the intervals overlap slightly, so that gap is likely real but less certain.

## Limitations

- **Small test set** (72 images), as above. Cross-validation over the whole dataset would give a steadier estimate.
- **CNN results vary between runs.** No random seed is fixed. An earlier run of this same notebook reached 97.22% (70 of 72), so expect a difference of a point or two.
- **The validation accuracy of 100% is also on only 72 images**, so it should not be read as a promise of perfect performance.
- **The tuning is not equal for all models.** The SVM and Random Forest were tuned with small cross-validated grids (kept small because of Colab compute time). The CNN architecture was chosen by hand and not searched.
- **HOG used the default scikit-image settings.** Different cell sizes or settings could change the classical results, especially the Random Forest.
- **Possible improvements:** transfer learning from a pretrained network such as ResNet, stronger augmentation (rotation, brightness, zoom), replacing Flatten with global average pooling to shrink the 17M-parameter Dense layer, batch normalization, and k-fold cross-validation for all models.

---

## Run it yourself

The notebook was written and run on **Google Colab**. The CNN took roughly 22 to 24 seconds per epoch there, and the SVM grid search took several minutes because HOG vectors are large.

1. Clone the repository:
   ```bash
   git clone https://github.com/swatiaggrawal/Metal-Defect-Detection.git
   cd Metal-Defect-Detection
   ```
2. Install the libraries (Colab already has most of them):
   ```bash
   pip install tensorflow scikit-learn scikit-image matplotlib seaborn pandas numpy pillow
   ```
3. Get the dataset from the [Kaggle page](https://www.kaggle.com/datasets/fantacher/neu-metal-surface-defects-data) and unzip it so that it contains `train`, `valid` and `test` folders, each with one subfolder per class. If the Kaggle command line download returns a 403 error, download the zip in your browser instead.
4. Open `CV_project.ipynb` in Colab or Jupyter. In Section 2, set the three folder paths to where you put the data:
   ```python
   train_dir = 'path/to/NEU Metal Surface Defects Data/train'
   test_dir  = 'path/to/NEU Metal Surface Defects Data/test'
   valid_dir = 'path/to/NEU Metal Surface Defects Data/valid'
   ```
5. Run all cells from the top. Use a GPU runtime for the CNN section.

## Notebook outline

1. Setup and imports
2. Load data, fix corrupted images, class distribution, sample images
3. PCA and t-SNE visualizations of the training images
4. CNN: build, train with callbacks, training curves, test evaluation, confusion matrix
5. SVM: HOG features, grid search, test evaluation, confusion matrix
6. Random Forest: grid search, test evaluation, confusion matrix
7. Model comparison chart and a closer look at the confused classes
8. Confidence intervals for the test accuracies

## Tools used

TensorFlow/Keras, scikit-learn, scikit-image, NumPy, Pandas, Matplotlib, Seaborn, Pillow, Google Colab.

## License

Built for academic purposes in the Computer Vision course at Sapienza University of Rome. The NEU dataset has its own license, which is listed on the Kaggle dataset page.
