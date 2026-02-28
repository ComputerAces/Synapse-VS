# 🧩 Math Nodes

This document covers nodes within the **Math** core category.

## 📂 Advanced

### Clamp

**Version**: `2.1.0`

Restricts a numerical value to a defined range [Min, Max].
If the value is outside the range, it is set to the nearest boundary.

Inputs:
- Flow: Trigger the clamp operation.
- Value: The number to restrict.
- Min: The lower boundary.
- Max: The upper boundary.

Outputs:
- Flow: Triggered after processing.
- Result: The clamped value.

---

### Exp

**Version**: `2.1.0`

Exponential Function (e^x). Calculates the result of Euler's number (e ≈ 2.71828) raised to the power of the input 'Value'.

This node is the inverse of the natural logarithm (LN). It is fundamental in modeling processes that grow or decay 
proportionally to their current value, such as population dynamics, radioactive decay, and continuously compounded interest.

Inputs:
- Flow: Trigger the calculation.
- Value: The exponent (x) for 'e'.

Outputs:
- Flow: Triggered after calculation completion.
- Result: The calculated value (e^Value).

---

### Inverse Lerp

**Version**: `2.1.0`

Calculates the normalized interpolant (T) for a value within a specific range [A, B].

This is the inverse of the Lerp operation. It determines where 'Value' sits 
relative to A and B.

Inputs:
- Flow: Trigger the calculation.
- A: The lower bound (maps to 0.0).
- B: The upper bound (maps to 1.0).
- Value: The number to normalize.

Outputs:
- Flow: Triggered after calculation.
- T: The normalized position (0.0 to 1.0).

---

### Lerp

**Version**: `2.1.0`

Performs Linear Interpolation (Lerp) between two values based on a weight factor.

Formula: Result = A + (B - A) * T. 
If T is 0.0, the result is A. If T is 1.0, the result is B.

Inputs:
- Flow: Trigger the calculation.
- A: The start value (0%).
- B: The end value (100%).
- T: The interpolation factor (typically 0.0 to 1.0).

Outputs:
- Flow: Triggered after calculation.
- Result: The interpolated value.

---

### Log10

**Version**: `2.1.0`

Calculates the base-10 logarithm of a given value.
Input must be a positive number.

Inputs:
- Flow: Trigger the calculation.
- Value: The positive number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The base-10 logarithm.

---

### Logarithm

**Version**: `2.1.0`

Calculates the logarithm of a value to a specified base.
Handles mathematical undefined cases (non-positive values) through an Error Flow.

Inputs:
- Flow: Trigger the calculation.
- Value: The positive number to calculate the log for.
- Base: The logarithmic base (defaults to e).

Outputs:
- Flow: Triggered after success.
- Result: The calculated logarithm.
- Error Flow: Triggered if the input is non-positive or calculation fails.

---

### Max

**Version**: `2.1.0`

Returns the larger of two numerical inputs.

Inputs:
- Flow: Trigger the comparison.
- A: First number.
- B: Second number.

Outputs:
- Flow: Triggered after comparison.
- Result: The maximum of A and B.

---

### Min

**Version**: `2.1.0`

Returns the smaller of two numerical inputs.

Inputs:
- Flow: Trigger the comparison.
- A: First number.
- B: Second number.

Outputs:
- Flow: Triggered after comparison.
- Result: The minimum of A and B.

---

### Power

**Version**: `2.1.0`

Calculates the power of a base number raised to an exponent.
Supports negative exponents and fractional bases.

Inputs:
- Flow: Trigger the calculation.
- Base: The number to be raised.
- Exponent: The power to raise the base to.

Outputs:
- Flow: Triggered after calculation.
- Result: The calculated power.

---

### Remap

**Version**: `2.1.0`

Linearly maps a value from one range [In Min, In Max] to another [Out Min, Out Max].
Commonly used for normalizing sensor data or scaling inputs for UI elements.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value to remap.
- In Min: The lower bound of the input range.
- In Max: The upper bound of the input range.
- Out Min: The lower bound of the output range.
- Out Max: The upper bound of the output range.

Outputs:
- Flow: Pulse triggered after calculation.
- Result: The remapped value.

---

### Sqrt

**Version**: `2.1.0`

Calculates the square root of a given numerical value.
Ensures the input is non-negative (clamped to 0) to avoid imaginary results.

Inputs:
- Flow: Trigger the calculation.
- Value: The number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The square root of the input.

---

## 📂 Arithmetic

### Abs

**Version**: `2.1.0`

Calculates the absolute value (magnitude) of a numerical input.
Ensures the result is non-negative.

Inputs:
- Flow: Trigger the calculation.
- Value: The number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The absolute value of the input.

---

### Add

**Version**: `2.1.0`

Combines two values using addition, string concatenation, or list merging.
Automatically detects data types and applies the appropriate combination logic.

Inputs:
- Flow: Trigger the addition process.
- A: The first value (Number, String, or List).
- B: The second value (Number, String, or List).

Outputs:
- Flow: Triggered after combination.
- Result: The sum, merged list, or concatenated string.

---

### Divide

**Version**: `2.1.0`

Divides two numbers and provides the quotient.

Inputs:
- Flow: Execution trigger.
- A: The dividend.
- B: The divisor.
- Handle Div 0: If true, returns 0 instead of triggering Error Flow on division by zero.

Outputs:
- Flow: Triggered on successful division.
- Error Flow: Triggered if division by zero occurs and not handled.
- Result: The quotient.

---

### Modulo

**Version**: `2.1.0`

Calculates the remainder of a division (modulo operation).

Inputs:
- Flow: Trigger the calculation.
- A: The dividend.
- B: The divisor.

Outputs:
- Flow: Triggered after calculation.
- Result: A modulo B.

---

### Multiply

**Version**: `2.1.0`

Performs multiplication of two numeric values.
Automatically handles integer and float conversion for the result.

Inputs:
- Flow: Trigger the multiplication.
- A: The first factor.
- B: The second factor.

Outputs:
- Flow: Triggered after the product is calculated.
- Result: The product of A and B.

---

### Subtract

**Version**: `2.1.0`

Subtracts one value from another. Supports both numeric subtraction 
and date/time offsets (subtracting seconds or days from a timestamp).

Inputs:
- Flow: Trigger the calculation.
- A: The base value (Number or Formatted Datetime).
- B: The value to subtract (Number).

Outputs:
- Flow: Triggered after the difference is calculated.
- Result: The resulting difference or offset date.

---

## 📂 Constants

### E

**Version**: `2.1.0`

Outputs the mathematical constant e (Euler's number, 2.71828...).

Inputs:
- Flow: Trigger the output.

Outputs:
- Flow: Triggered after output.
- Result: The value of e.

---

### Pi

**Version**: `2.1.0`

Outputs the mathematical constant Pi (3.14159...).

Inputs:
- Flow: Trigger the output.

Outputs:
- Flow: Triggered after output.
- Result: The value of Pi.

---

## 📂 Hyperbolic

### Cosh

**Version**: `2.1.0`

Calculates the hyperbolic cosine of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic cosine.

---

### Sinh

**Version**: `2.1.0`

Calculates the hyperbolic sine of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic sine.

---

### Tanh

**Version**: `2.1.0`

Calculates the hyperbolic tangent of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic tangent.

---

## 📂 Logic

### AND

**Version**: `2.1.0`

Performs a logical AND operation on a set of boolean inputs.
Returns True only if all provided inputs are True.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate (supports dynamic expansion).

Outputs:
- Flow: Triggered after evaluation.
- Result: True if all inputs are True, False otherwise.

---

### Boolean Flip

**Version**: `2.1.0`

Inverts the provided boolean value (True becomes False, and vice-versa).

Inputs:
- Flow: Trigger the inversion.
- Value: The boolean value to flip.

Outputs:
- Flow: Triggered after the flip.
- Result: The inverted boolean result.

---

### NAND

**Version**: `2.1.0`

Performs a logical NAND operation.

Returns True if at least one input is False. Returns False only 
if all provided inputs are True. Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The NAND result.

---

### NOR

**Version**: `2.1.0`

Performs a logical NOR operation.

Returns True only if all provided inputs are False. Returns False 
 if at least one input is True. Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The NOR result.

---

### NOT

**Version**: `2.1.0`

Logical NOT operator. Inverts the input boolean.

Inputs:
- Flow: Trigger execution.
- In: The input boolean value.

Outputs:
- Flow: Triggered after inversion.
- Result: The inverted result.

---

### OR

**Version**: `2.1.0`

Performs a logical OR operation on a set of boolean inputs.

Returns True if at least one of the provided inputs is True. 
Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: True if any input is True, False otherwise.

---

### XNOR

**Version**: `2.1.0`

Performs a logical XNOR operation.

Returns True if an even number of inputs are True. Supports 
dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The XNOR result.

---

### XOR

**Version**: `2.1.0`

Performs a logical XOR (Exclusive OR) operation.

Returns True if an odd number of inputs are True. Supports 
dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: True if the XOR condition is met.

---

## 📂 Random

### Random

**Version**: `2.1.0`

Generates a pseudo-random number or currency value within a specified range.
Supports both integer 'Number' and decimal 'Currency' (2 decimal places) types.

Inputs:
- Flow: Trigger the random generation.
- Min: The minimum value of the range.
- Max: The maximum value of the range.
- Random Type: The type of output ('Number' or 'Currency').

Outputs:
- Flow: Pulse triggered after generation.
- Result: The generated random value.

---

## 📂 Rounding

### Ceil

**Version**: `2.1.0`

Rounds a numerical value up to the nearest integer.

Inputs:
- Flow: Trigger the ceiling operation.
- Value: The number to round up.

Outputs:
- Flow: Triggered after rounding.
- Result: The resulting integer.

---

### Floor

**Version**: `2.1.0`

Rounds a numerical value down to the nearest integer that is less than or equal to the input.

Unlike standard rounding which may round up or down depending on the decimal part, Floor always moves 
the value towards negative infinity. 
Example: 3.7 -> 3.0, -3.2 -> -4.0.

Inputs:
- Flow: Trigger the floor operation.
- Value: The number to round down.

Outputs:
- Flow: Triggered after the value is processed.
- Result: The largest integer less than or equal to 'Value'.

---

### Round

**Version**: `2.1.0`

Rounds a numerical value to a specified number of decimal places.

Inputs:
- Flow: Trigger the round operation.
- Value: The number to round.
- Decimals: The number of decimal places to keep.

Outputs:
- Flow: Triggered after rounding.
- Result: The rounded number.

---

## 📂 Trigonometry

### Acos

**Version**: `2.1.0`

Calculates the arc cosine (inverse cosine) of a value.
The input value must be between -1 and 1.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process (-1 to 1).

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

---

### Asin

**Version**: `2.1.0`

Calculates the arc sine (inverse sine) of a value.
The input value must be between -1 and 1.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process (-1 to 1).

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

---

### Atan

**Version**: `2.1.0`

Calculates the arc tangent (inverse tangent) of a value.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

---

### Atan2

**Version**: `2.1.0`

Calculates the arc tangent of Y/X, handling quadrant information correctly.
Ensures a result in the full 360-degree (2*pi) range.

Inputs:
- Flow: Trigger the calculation.
- Y: The y-coordinate value.
- X: The x-coordinate value.

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

---

### Cos

**Version**: `2.1.0`

Calculates the cosine of a given angle.
Supports both Degrees and Radians based on the Degrees property.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The cosine of the angle.

---

### Degrees To Radians

**Version**: `2.1.0`

Converts an angle from degrees to radians.

Inputs:
- Flow: Trigger the conversion.
- Degrees: The angle in degrees.

Outputs:
- Flow: Triggered after conversion.
- Result: The angle in radians.

---

### Radians To Degrees

**Version**: `2.1.0`

Converts an angle from radians to degrees.

Inputs:
- Flow: Trigger the conversion.
- Radians: The angle in radians.

Outputs:
- Flow: Triggered after conversion.
- Result: The angle in degrees.

---

### Sin

**Version**: `2.1.0`

Calculates the sine of a given angle.

Processes the input 'Angle'. If 'Degrees' is True, the angle is 
treated as degrees and converted to radians before calculation. 
Otherwise, it is treated as radians.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.
- Degrees: Whether the angle is in degrees (True) or radians (False).

Outputs:
- Flow: Triggered after calculation.
- Result: The sine of the angle.

---

### Tan

**Version**: `2.1.0`

Calculates the tangent of a given angle.

Processes the input 'Angle'. If 'Degrees' is True, the angle is 
treated as degrees and converted to radians before calculation. 
Otherwise, it is treated as radians.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.
- Degrees: Whether the angle is in degrees (True) or radians (False).

Outputs:
- Flow: Triggered after calculation.
- Result: The tangent of the angle.

---

[Back to Node Index](Index.md)
