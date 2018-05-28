from __future__ import absolute_import, division, print_function

import os
import matplotlib.pyplot as plt

import tensorflow as tf
import tensorflow.contrib.eager as tfe

tf.enable_eager_execution()


data_url = "http://download.tensorflow.org/data/iris_training.csv"
dataset_fp = tf.keras.utils.get_file(
  fname = os.path.basename(data_url),
  origin = data_url
)

print("Local copy of dataset: {}".format(dataset_fp))


def parseFile(line):
  example_defaults = [[0.], [0.], [0.], [0.], [0]]
  parsed_line = tf.decode_csv(line, example_defaults)

  # First 4 fields are features, combine into single tensor
  features = tf.reshape(parsed_line[:-1], shape=(4,))

  # Last one is the line number
  label = tf.reshape(parsed_line[-1], shape=())
  return features, label

train_dataset = tf.data.TextLineDataset(dataset_fp)
# skip the header row
train_dataset = train_dataset.skip(1) 

# transform each line into it's features and labels
train_dataset = train_dataset.map(parseFile) 

# shuffle around the lines
train_dataset = train_dataset.shuffle(buffer_size = 1000)

# gather 32 samples
train_dataset = train_dataset.batch(32)

# get one
features, label = iter(train_dataset).next()

# define the model
model = tf.keras.Sequential([
  tf.keras.layers.Dense(10, activation = "relu", input_shape = (4,)),
  tf.keras.layers.Dense(10, activation = "relu"),
  tf.keras.layers.Dense(3) # because we have 3 output classes
])

# define the loss
def loss(model, x, y):
  y_hat = model(x)
  return tf.losses.sparse_softmax_cross_entropy(labels = y, logits = y_hat)

# define the gradient
def grad(model, inputs, targets):
  with tf.GradientTape() as tape:
    loss_value = loss(model, inputs, targets)
  return tape.gradient(loss_value, model.variables)

# define the optimizer
optimizer = tf.train.GradientDescentOptimizer(learning_rate = .01)

# now train the model!

"""
1. Iterate each epoch. An epoch is one pass through the dataset.
2. Within an epoch, iterate over each example in the training Dataset grabbing its features (x) and label (y).
3. Using the example's features, make a prediction and compare it with the label. Measure the inaccuracy of the prediction and use that to calculate the model's loss and gradients.
4. Use an optimizer to update the model's variables.
5. Keep track of some stats for visualization.
6. Repeat for each epoch.
"""

train_loss_results = []
train_accuracy_results = []

num_epochs = 201;
for epoch in range(num_epochs):
  epoch_loss_avg = tfe.metrics.Mean()
  epoch_accuracy = tfe.metrics.Accuracy()

  for x, y in train_dataset:
    # optimize model
    grads = grad(model, x, y)
    optimizer.apply_gradients(zip(grads, model.variables), global_step=tf.train.get_or_create_global_step())

    # keep track of loss
    epoch_loss_avg(loss(model, x, y))
    prediction = tf.argmax(model(x), axis=1, output_type = tf.int32)
    epoch_accuracy(prediction, y)

  # end the epoch
  train_loss_results.append(epoch_loss_avg.result())
  train_accuracy_results.append(epoch_accuracy.result())

  if epoch % 50 == 0:
    print("Epoch {:03d}: Loss: {:.3f}, Accuracy: {:.3%}".format(epoch,
                                                                epoch_loss_avg.result(),
                                                                epoch_accuracy.result()))

fig, axes = plt.subplots(2, sharex=True, figsize=(12, 8))
fig.suptitle('Training Metrics')

axes[0].set_ylabel('Loss')
axes[0].plot(train_loss_results)

axes[1].set_ylabel("Accuracy", fontsize=14)
axes[1].set_xlabel("Epoch", fontsize=14)
axes[1].plot(train_accuracy_results)

plt.show()

test_url = "http://download.tensorflow.org/data/iris_test.csv"
test_dataset = tf.keras.utils.get_file(
  fname = os.path.basename(test_url),
  origin = test_url
)

test_dataset = tf.data.TextLineDataset(test_dataset)
test_dataset = test_dataset.skip(1)             # skip header row
test_dataset = test_dataset.map(parseFile)      # parse each row with the funcition created earlier
test_dataset = test_dataset.shuffle(1000)       # randomize
test_dataset = test_dataset.batch(32)

test_accuracy = tfe.metrics.Accuracy()

for (x, y) in test_dataset:
  prediction = tf.argmax(model(x), axis=1, output_type = tf.int32)
  test_accuracy(prediction, y)

print("Test set accuracy: {:.3%}".format(test_accuracy.result()))

class_ids = ["Iris setosa", "Iris versicolor", "Iris virginica"]

predict_dataset = tf.convert_to_tensor([
  [5.1, 3.3, 1.7, 0.5,],
  [5.9, 3.0, 4.2, 1.5,],
  [6.9, 3.1, 5.4, 2.1]
])

predictions = model(predict_dataset)

for i, logits in enumerate(predictions):
  class_idx = tf.argmax(logits).numpy()
  name = class_ids[class_idx]

  print("Example {} prediction: {}".format(i, name))