# coding=utf-8
import json
import os
import sys

from sklearn import linear_model, datasets
from sklearn.metrics import f1_score, accuracy_score, roc_auc_score, log_loss, plot_confusion_matrix, \
    classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Ensure result is reproducible
RANDOM_SEED = 42

# Step 1: Set up target metrics for evaluating training

# Define a target loss metric to aim for
target_f1 = 0.9

# instantiate classifier and scaler
clf = linear_model.RidgeClassifier()
scaler = StandardScaler()

# Step 2: Perform training for model

# get training data
wine = datasets.load_wine()
X = wine.data
y = wine.target
class_names = wine.target_names
feat_names = wine.feature_names

# split train and test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, shuffle=True,
                                                    random_state=RANDOM_SEED)

# scale data points
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# train model
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)

# Step 3: Evaluate the quality of the trained model

# print classification report of classifier
print(classification_report(y_test, y_pred, target_names=class_names))

# evaluate the quality of the trained model using weighted f1 score
f1_metric = f1_score(y_test, y_pred, average='weighted')
print(f"f1 score: {round(f1_metric, 3)}")

# Only persist the model if we have passed our desired threshold
if f1_metric < target_f1:
    sys.exit('Training failed to meet threshold')

# Step 4: Persist the trained model in ONNX format in the local file system along with any significant metrics

# persist model
initial_type = [('float_input', FloatTensorType([None, 4]))]
onx = convert_sklearn(clf, initial_types=initial_type)
with open("model.onnx", "wb") as f:
    f.write(onx.SerializeToString())

# calculate set of quality metrics
accuracy_metric = accuracy_score(y_test, y_pred)

# write metrics
if not os.path.exists("metrics"):
    os.mkdir("metrics")

with open("metrics/f1.metric", "w+") as f:
    json.dump(f1_metric, f)
with open("metrics/accuracy.metric", "w+") as f:
    json.dump(accuracy_metric, f)

confusion_metrics = plot_confusion_matrix(clf, X_test, y_test, display_labels=class_names, cmap=plt.cm.Blues)
confusion_metrics.ax_.set_title("Confusion matrix of Ridge classifier on Wine dataset")
plt.savefig('metrics/confusion_matrix.png')
plt.clf()
