import random
from statistics import mode
from typing import Tuple, List, Dict, Optional
class MathFactory:
    @staticmethod
    def get_level_settings(level, mode):
        ranges = {"Easy": 10, "Intermediate": 100, "Expert": 1000}
        num_range = ranges.get(level, 10)

        time_map = {
        "Easy": {"Rapid": 26, "Blitz": 13, "Bullet": 7},
        "Intermediate": {"Rapid": 21, "Blitz": 10, "Bullet": 5},
        "Expert": {"Rapid": 16, "Blitz": 7, "Bullet": 3}
        }

        seconds_allowed = time_map[level][mode]

        return num_range, seconds_allowed

    @staticmethod
    def generate_question(op_type: str, sub_level: int) -> Tuple[str, int, List[int]]:
        """Generate a question and four MCQ options for the given operation.

        Supports:
        - Addition, Subtraction (levels 1-8 digit-based)
        - Multiplication, Division (levels 1-4 digit-based)
        - Squares, Cubes, Square Root, Cube Root (levels 1-4 range-based)
        - Mixed (randomly picks from the four basic operations)
        """

        # Normalize operation names (accept common aliases)
        if isinstance(op_type, str):
            op_key = op_type.strip().lower()
        else:
            op_key = str(op_type).strip().lower()

        op_aliases = {
            "addition": "Addition",
            "add": "Addition",
            "subtraction": "Subtraction",
            "sub": "Subtraction",
            "multiplication": "Multiplication",
            "multiply": "Multiplication",
            "mul": "Multiplication",
            "division": "Division",
            "divide": "Division",
            "div": "Division",
            "mixed": "Mixed",

            # Powers / roots
            "squares": "Squares",
            "square": "Squares",
            "sq": "Squares",
            "cubes": "Cubes",
            "cube": "Cubes",
            "cb": "Cubes",
            "square root": "Sq Roots",
            "squareroot": "Sq Roots",
            "sqroot": "Sq Roots",
            "sqrt": "Sq Roots",
            "cube root": "Cube Roots",
            "cuberoot": "Cube Roots",
            "croot": "Cube Roots",
            "cbrt": "Cube Roots",
        }

        op_type = op_aliases.get(op_key, op_type)

        if op_type == "Mixed":
            op_type = random.choice(["Addition", "Subtraction", "Multiplication", "Division"])
            if op_type in ["Addition", "Subtraction"]:
                # Level N maps to internal (2N-1) or (2N) for add/sub difficulty
                sub_level = random.choice([(sub_level * 2) - 1, sub_level * 2])

        # Helper to get a random number with a specific number of digits
        def get_num_with_digits(d: int) -> int:
            if d == 1:
                return random.randint(1, 9)
            return random.randint(10**(d - 1), (10**d) - 1)

        # --- ADDITION & SUBTRACTION LOGIC (Levels 1-8) ---
        if op_type in ["Addition", "Subtraction"]:
            # Mapping levels to digit pairs (d1, d2)
            digit_map = {1:(1,1), 2:(1,2), 3:(1,3), 4:(1,4), 5:(2,2), 6:(2,3), 7:(3,3), 8:(4,4)}
            d1, d2 = digit_map.get(sub_level, (1,1))
            
            # Subtraction can have d1-d2 or d2-d1 as long as result is positive
            a, b = get_num_with_digits(d1), get_num_with_digits(d2)
            
            if op_type == "Addition":
                ans = a + b
                q_text = f"{a} + {b}"
            else:
                # Ensure subtraction stays positive for students
                high, low = (a, b) if a >= b else (b, a)
                ans = high - low
                q_text = f"{high} - {low}"

        # --- MULTIPLICATION & DIVISION LOGIC (Levels 1-4) ---
        elif op_type in ["Multiplication", "Division"]:
            # Mapping levels to digit pairs: 1=1x1, 2=1x2, 3=1x3, 4=2x2
            digit_map = {1:(1,1), 2:(1,2), 3:(1,3), 4:(2,2)}
            d1, d2 = digit_map.get(sub_level, (1,1))
            
            if op_type == "Multiplication":
                a, b = get_num_with_digits(d1), get_num_with_digits(d2)
                ans = a * b
                q_text = f"{a} × {b}"
            else:
                # Ensure clean division: (Result * Divisor) / Divisor
                divisor = get_num_with_digits(d1)
                ans = get_num_with_digits(d2)
                dividend = divisor * ans
                q_text = f"{dividend} ÷ {divisor}"

        # --- POWERS & ROOTS LOGIC (Levels 1-4) ---
        elif op_type in ["Squares", "Cubes", "Sq Roots", "Cube Roots"]:
            # Define base ranges per sub_level to keep answers student-friendly
            if op_type in ["Squares", "Sq Roots"]:
                # Slightly larger bases are OK for squares
                # Level 1: 1-9, 2: 5-15, 3: 10-20, 4: 15-25
                sq_ranges = {
                    1: (1, 25),
                    2: (25, 50),
                    3: (50, 100),
                    4: (100, 125),
                }
                low, high = sq_ranges.get(sub_level, (1, 15))
                base = random.randint(low, high)

                if op_type == "Squares":
                    ans = base ** 2
                    q_text = f"{base}²"
                else:  # Sq Roots
                    value = base ** 2
                    ans = base
                    q_text = f"√{value}"

            else:
                # Cubes / Cube Roots: keep bases small to avoid huge numbers
                # Level 1: 1-5, 2: 2-6, 3: 3-7, 4: 4-8
                cb_ranges = {
                    1: (1, 25),
                    2: (25, 50),
                    3: (50, 75),
                    4: (75, 100),
                }
                low, high = cb_ranges.get(sub_level, (1, 5))
                base = random.randint(low, high)

                if op_type == "Cubes":
                    ans = base ** 3
                    q_text = f"{base}³"
                else:  # Cube Roots
                    value = base ** 3
                    ans = base
                    q_text = f"∛{value}"

        # --- OPTION GENERATION ---
        opts = {ans}
        while len(opts) < 4:
            # Variance scales based on answer magnitude

            if ans > 200:
                variance = max(3, int(ans * 0.001))
                delta = 10 * random.randint(-variance, variance)

            elif ans > 50:
                if len(opts) < 3:
                    delta = random.choice([-10, 10])
                else:
                    delta = random.randint(-2, 2)

            else:  # ans <= 50
                delta = random.randint(-5, 5)

            candidate = ans + delta

            if candidate > 0 and candidate != ans:
                opts.add(candidate)
        
        opts_list = list(opts)
        random.shuffle(opts_list)
        return q_text, ans, opts_list

    @staticmethod
    def generate_t20_question(config: dict) -> Tuple[str, int, List[int]]:
        """
        Generates a question based on a specific configuration dictionary.
        Targeted for T20 mode.
        config example: {"type": "mul", "a_digits": 2, "b_digits": 2, "range": (11, 19)}
        """

        # Helper to get a random number with a specific number of digits
        def get_num_with_digits(d):
            if d == 1: 
                return random.randint(2, 9)
            return random.randint(10**(d-1), (10**d)-1)

        q_type = config.get("type", "add")
        
        # --- ADDITION ---
        if q_type == "add":
            a_digits = config.get("a_digits", 1)
            b_digits = config.get("b_digits", 1)
            a = get_num_with_digits(a_digits)
            b = get_num_with_digits(b_digits)
            ans = a + b
            q_text = f"{a} + {b}"

        # --- SUBTRACTION ---
        elif q_type == "sub":
            a_digits = config.get("a_digits", 1)
            b_digits = config.get("b_digits", 1)
            a = get_num_with_digits(a_digits)
            b = get_num_with_digits(b_digits)
            # Ensure positive result
            high, low = (a, b) if a >= b else (b, a)
            ans = high - low
            q_text = f"{high} - {low}"

        # --- MULTIPLICATION ---
        elif q_type == "mul":
            a_digits = config.get("a_digits", 1)
            b_digits = config.get("b_digits", 1)
            r_range = config.get("range", None)
            
            if r_range:
                # If range is provided, use it for 'a'
                a = random.randint(r_range[0], r_range[1])
                # 'b' uses digit count
                b = random.randint(r_range[0], r_range[1])
            else:
                a = get_num_with_digits(a_digits)
                b = get_num_with_digits(b_digits)
            
            ans = a * b
            q_text = f"{a} × {b}"

        # --- DIVISION ---
        elif q_type == "div":
            # "num_digits": Dividend digits | "den_digits": Divisor digits
            num_digits = config.get("num_digits", 2) 
            den_digits = config.get("den_digits", 1) 
            
            # Generate Divisor
            divisor = get_num_with_digits(den_digits)
            
            # Find a Dividend with 'num_digits' that is a multiple of divisor
            min_div = 10**(num_digits-1) if num_digits > 1 else 1
            max_div = (10**num_digits) - 1
            
            start = (min_div // divisor) 
            if start * divisor < min_div: start += 1
            end = max_div // divisor
            
            if start > end:
                # Fallback
                divisor = get_num_with_digits(1)
                start, end = 1, 9
            
            quotient = random.randint(start, end)
            dividend = quotient * divisor
            
            ans = quotient
            q_text = f"{dividend} ÷ {divisor}"

        # Fallback
        else:
            return "1 + 1", 2, [1, 2, 3, 4]
        
        # --- OPTION GENERATION ---
        opts = {ans}
        while len(opts) < 4:
           # Variance scales based on answer magnitude

            if ans > 200:
                variance = max(3, int(ans * 0.001))
                delta = 10 * random.randint(-variance, variance)

            elif ans > 50:
                if len(opts) < 3:
                    delta = random.choice([-10, 10])
                else:
                    delta = random.randint(-2, 2)

            else:  # ans <= 50
                delta = random.randint(-5, 5)

            candidate = ans + delta

            if candidate > 0 and candidate != ans:
                opts.add(candidate)
                    
        opts_list = list(opts)
        random.shuffle(opts_list)
        return q_text, ans, opts_list