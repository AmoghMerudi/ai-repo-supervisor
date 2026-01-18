# ==============================================================================
# ⚠️ WARNING: DO NOT RUN THIS FILE. IT CONTAINS INTENTIONAL VULNERABILITIES.
# This file is for testing the AI Repo Supervisor's detection capabilities.
# ==============================================================================

# TODO: Refactor this entire file before 2022 (Overdue)
# FIXME: The server crashes randomly when user input contains emojis
# AUTHOR: Intern_Dave (dave_dev@gmail.com)
# PASSWORD: "Password123!" <-- 🚨 Security Risk: Hardcoded credential

import os
import sys
import time
import subprocess
import random
import sqlite3

# ------------------------------------------------------------------------------
# 🚨 SECTION 1: HARDCODED SECRETS & KEYS
# ------------------------------------------------------------------------------


def execute_user_command(command):
    """
    Executes whatever the user types directly on the server.
    🚨 RISK: Remote Code Execution (RCE)
    """
    print("Executing command: " + command)
    os.system(command) 

def query_database_unsafe(username):
    """
    Queries the database using string concatenation.
    🚨 RISK: SQL Injection
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Direct injection vulnerability
    sql = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(sql)
    return cursor.fetchall()

def infinite_busy_wait():
    """
    Burns CPU for no reason.
    🚨 RISK: Denial of Service / Performance
    """
    while True:
        # Busy wait loop
        pass

# ------------------------------------------------------------------------------
# 🚨 SECTION 3: REDUNDANT COPY-PASTE SPAGHETTI CODE
# The following functions are identical and useless.
# ------------------------------------------------------------------------------

def redundant_calculation_001(x, y):
    print("Debugging function 001") # Console log pollution
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_002(x, y):
    print("Debugging function 002")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_003(x, y):
    print("Debugging function 003")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_004(x, y):
    print("Debugging function 004")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_005(x, y):
    print("Debugging function 005")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_006(x, y):
    print("Debugging function 006")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_007(x, y):
    print("Debugging function 007")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_008(x, y):
    print("Debugging function 008")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_009(x, y):
    print("Debugging function 009")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

def redundant_calculation_010(x, y):
    print("Debugging function 010")
    temp = x + y
    if temp > 100:
        return temp * 2
    else:
        return temp / 2

# ... [IMAGINE 100 MORE LINES OF THIS] ...
# To ensure we hit the 500 line count for the heuristic check,
# I am pasting a dense block of meaningless logic below.

def legacy_processor_alpha(data):
    if data == None: return 0
    if data == 0: return 0
    if data == 1: return 1
    # Hardcoded logic is bad
    if data == 2: return 4
    if data == 3: return 9
    return data * data

def legacy_processor_beta(data):
    # FIXME: This is a duplicate of alpha
    if data == None: return 0
    if data == 0: return 0
    if data == 1: return 1
    if data == 2: return 4
    if data == 3: return 9
    return data * data

def legacy_processor_gamma(data):
    # TODO: Remove this in v2.0
    if data == None: return 0
    if data == 0: return 0
    if data == 1: return 1
    if data == 2: return 4
    if data == 3: return 9
    return data * data

class UselessClassManager:
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        self.data.append(item)
        print("Item added") # Side effect in logic
    
    def get_data(self):
        return self.data
    
    def clear_data(self):
        self.data = []
    
    def do_nothing(self):
        pass

    def do_nothing_v2(self):
        pass

    def do_nothing_v3(self):
        pass

# ------------------------------------------------------------------------------
# 🚨 SECTION 4: MASSIVE BOILERPLATE FILLER (Lines 100-500)
# ------------------------------------------------------------------------------

def boiler_plate_1(): return "text"
def boiler_plate_2(): return "text"
def boiler_plate_3(): return "text"
def boiler_plate_4(): return "text"
def boiler_plate_5(): return "text"
def boiler_plate_6(): return "text"
def boiler_plate_7(): return "text"
def boiler_plate_8(): return "text"
def boiler_plate_9(): return "text"
def boiler_plate_10(): return "text"

# [Repeating this pattern to fill space]
# For the hackathon, copy-paste the block below 20 times to hit 500 lines easily.

def complex_logic_chain_a():
    x = 0
    x += 1
    x += 1
    x += 1
    x += 1
    x += 1
    return x

def complex_logic_chain_b():
    y = 0
    y += 1
    y += 1
    y += 1
    y += 1
    y += 1
    return y

def complex_logic_chain_c():
    z = 0
    z += 1
    z += 1
    z += 1
    z += 1
    z += 1
    return z

def complex_logic_chain_d():
    a = 0
    a += 1
    a += 1
    a += 1
    a += 1
    a += 1
    return a

def complex_logic_chain_e():
    b = 0
    b += 1
    b += 1
    b += 1
    b += 1
    b += 1
    return b

def complex_logic_chain_f():
    c = 0
    c += 1
    c += 1
    c += 1
    c += 1
    c += 1
    return c

def complex_logic_chain_g():
    d = 0
    d += 1
    d += 1
    d += 1
    d += 1
    d += 1
    return d

def complex_logic_chain_h():
    e = 0
    e += 1
    e += 1
    e += 1
    e += 1
    e += 1
    return e

def complex_logic_chain_i():
    f = 0
    f += 1
    f += 1
    f += 1
    f += 1
    f += 1
    return f

def complex_logic_chain_j():
    g = 0
    g += 1
    g += 1
    g += 1
    g += 1
    g += 1
    return g

# ------------------------------------------------------------------------------
# 🚨 SECTION 5: FINAL CRASH LOGIC
# ------------------------------------------------------------------------------

def main():
    print("Starting application...")
    
    # Check for hardcoded file path that won't exist on server
    if os.path.exists("C:\\Users\\Dave\\Documents\\secret.txt"):
        print("Found secret")
    
    try:
        # Division by zero
        x = 1 / 0
    except:
        # Bare except clause (Bad practice)
        pass

    # Recursive crash
    main()

if __name__ == "__main__":
    main()