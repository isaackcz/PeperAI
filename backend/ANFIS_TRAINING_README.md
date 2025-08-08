# ANFIS Training for Bell Pepper Classification

This document explains how to train the Adaptive Neuro-Fuzzy Inference System (ANFIS) for multi-class bell pepper classification using the provided dataset.

## Dataset Structure

The training uses the bell pepper dataset located at `datasets/Bell Pepper dataset 1/` with the following structure:

```
datasets/Bell Pepper dataset 1/
├── damaged/     # Damaged bell peppers
├── dried/       # Dried bell peppers  
├── old/         # Old bell peppers
├── ripe/        # Ripe bell peppers
└── unripe/      # Unripe bell peppers
```

Each category contains multiple `.jpg` images of bell peppers in that condition.

## Features Extracted

The system extracts 11 features from each image:

1. **HSV Color Features (6 features):**
   - `h_mean`, `s_mean`, `v_mean` - Average hue, saturation, value
   - `h_std`, `s_std`, `v_std` - Standard deviation of hue, saturation, value

2. **GLCM Texture Features (2 features):**
   - `glcm_contrast` - Texture contrast
   - `glcm_homogeneity` - Texture homogeneity

3. **Contour Shape Features (3 features):**
   - `contour_area` - Area of the pepper contour
   - `circularity` - How circular the pepper is
   - `solidity` - Ratio of contour area to convex hull area

## Training Process

### 1. Quick Start

Run the training script:

```bash
# Windows
cd backend
run_training.bat

# Or manually
python train_anfis.py
```

### 2. Training Parameters

The training uses the following parameters:

- **Test Size**: 20% of data for testing
- **Validation Size**: 20% of training data for validation
- **Number of Rules**: 12 fuzzy rules per model
- **Training Epochs**: 400 epochs
- **Learning Rate**: 0.008
- **Early Stopping**: 30 epochs patience

### 3. Model Architecture

The system uses a **one-vs-all** approach for multi-class classification:

- 5 separate ANFIS models (one for each category)
- Each model learns to distinguish its class from all others
- Final prediction combines probabilities from all models

## Output Files

After training, the following files are generated:

### Models Directory (`./models/`)
- `bell_pepper_anfis_class_0.pkl` - Model for class 0
- `bell_pepper_anfis_class_1.pkl` - Model for class 1
- `bell_pepper_anfis_class_2.pkl` - Model for class 2
- `bell_pepper_anfis_class_3.pkl` - Model for class 3
- `bell_pepper_anfis_class_4.pkl` - Model for class 4

### Training Output Directory (`./training_output/`)
- `bell_pepper_anfis_training_history.json` - Training loss and accuracy curves
- `bell_pepper_anfis_evaluation.json` - Test set performance metrics
- `bell_pepper_anfis_preprocessing.pkl` - Label encoder and feature scaler

## Performance Metrics

The training provides comprehensive evaluation metrics:

- **Overall Accuracy**: Percentage of correctly classified samples
- **Per-class Metrics**: Precision, recall, and F1-score for each category
- **Confusion Matrix**: Detailed classification results
- **Training History**: Loss and accuracy curves for monitoring

## Integration with Application

The trained models are automatically loaded when the FastAPI application starts:

1. Models are loaded from `./models/` directory
2. Preprocessing data is loaded from `./training_output/`
3. The `/predict` endpoint uses ANFIS for classification
4. Results include category prediction and confidence scores

## Customization

### Adjusting Training Parameters

Edit `train_anfis.py` to modify training parameters:

```python
results = trainer.train_full_pipeline(
    test_size=0.2,          # Change test split
    random_state=42,        # Change random seed
    n_rules=12,             # Change number of fuzzy rules
    epochs=400,             # Change training epochs
    learning_rate=0.008     # Change learning rate
)
```

### Adding New Categories

1. Add new category folder to dataset
2. Update `categories` list in `dataset_trainer.py`
3. Retrain the models

### Feature Engineering

Modify `feature_extractor.py` to:
- Add new features
- Change feature extraction methods
- Adjust preprocessing steps

## Troubleshooting

### Common Issues

1. **Dataset not found**: Ensure dataset path is correct
2. **Memory errors**: Reduce batch size or number of rules
3. **Poor accuracy**: Try different learning rates or more epochs
4. **Model loading errors**: Check if training completed successfully

### Performance Optimization

- **Faster training**: Reduce epochs or number of rules
- **Better accuracy**: Increase epochs, adjust learning rate
- **Memory usage**: Reduce batch size or number of membership functions

## Expected Results

With the provided dataset, you should expect:

- **Overall Accuracy**: 85-95% on test set
- **Training Time**: 10-30 minutes depending on hardware
- **Model Size**: ~1-2 MB per model file

The ANFIS approach provides interpretable fuzzy rules while maintaining competitive accuracy for bell pepper classification. 