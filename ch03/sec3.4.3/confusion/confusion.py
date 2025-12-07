
# sample: each element is:
# (actual temperature, predicted temperature)
temperature_log = [
    (20, 21), (25, 24), (30, 28), (15, 18), (22, 19), (27, 29),
    (18, 17), (21, 23), (16, 15), (20, 20), (24, 26), (19, 18),
    (23, 24), (28, 27), (19, 20), (17, 18), (22, 23), (26, 25),
    (29, 31), (21, 22), (18, 16), (24, 22), (20, 21), (25, 27)
]

# def. threshold for prediction as "accurate"
threshold = 2  # plus or minus 2 degrees range

true_positive = 0  # accurate positive predictions
false_positive = 0 # predicted higher, inaccurate
true_negative = 0  # accurate negative predictions
false_negative = 0 # predicted lower, inaccurate

# populate confusion matrix
for actual, predicted in temperature_log:
    difference = abs(actual - predicted)
    
    if difference <= threshold:
        # within acceptable range
        if predicted >= actual:
            true_positive += 1  # slightly higher or equal
        else:
            true_negative += 1  # slightly lower
    else:
        # outside acceptable range
        if predicted > actual:
            false_positive += 1  # overestimated and inaccurate
        else:
            false_negative += 1  # underestimated and inaccurate

print("Confusion matrix")
print(f"True Positives (TP): {true_positive}")
print(f"False Positives (FP): {false_positive}")
print(f"True Negatives (TN): {true_negative}")
print(f"False Negatives (FN): {false_negative}")

# optional: calculate metrics
accuracy = (true_positive + true_negative) / len(temperature_log)
precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0

print("\nPerformance metrics")
print(f"Accuracy: {accuracy:.2f}")
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
