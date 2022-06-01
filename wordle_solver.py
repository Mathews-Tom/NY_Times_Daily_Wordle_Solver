import os
import string
from collections import OrderedDict
from datetime import date
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

URL = "https://www.nytimes.com/games/wordle/index.html"
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 960

def split_word_evaluation(result, guess):
    """Split word evaluation to absent, present and correct"""
    absent = []
    present = []
    correct = []
    for i in range(0, len(result)):
        if result[i] == "a":
            absent.append(guess[i])
        elif result[i] == "p":
            present.append([guess[i], i])
        elif result[i] == "c":
            correct.append([guess[i], i])
    return (absent, present, correct)

def remove_incorrect_words(result, guess, possible_words):
    """Returns the list of words with incorrect possibilties removed"""
    absent, present, correct = split_word_evaluation(result, guess)
    good = []
    for ch in correct:
        good.append(ch[0])
    for ch in present:
        good.append(ch[0])
    
    acceptable_words1 = []
    for w in possible_words:
        check = 0
        for b in absent:
            if b in w:
                if b in good:
                    pass
                else:
                    check = 1
                    break
        if check == 0:
            acceptable_words1.append(w)

    acceptable_words2 = []
    for w in acceptable_words1:
        check = 0
        for g in correct:
            if w[g[1]] != g[0]:
                check = 1
                break
        if check == 0:
            acceptable_words2.append(w)
    
    acceptable_words3 = []
    for w in acceptable_words2:
        check = 0
        for p in present:
            if w[p[1]] == p[0]:
                check = 1
                break
        if check == 0:
            acceptable_words3.append(w)
    
    acceptable_words4 = []
    for w in acceptable_words3:
        check = 0
        for g in good:
            if g not in w:
                check = 1
                break
        if check == 0:
            acceptable_words4.append(w)

    acceptable_words5 = []
    for w in acceptable_words4:
        check = 0
        for b in absent:
            if b in good:
                if w.count(b) != good.count(b):
                    check = 1
                    break
        if check == 0:
            acceptable_words5.append(w)
    
    return acceptable_words5

def get_letter_frequency(possible_words):
    """Finds frequencies of letters in each position"""
    alphabet = string.ascii_uppercase
    arr = {}
    for c in alphabet:
        freq = [0, 0, 0, 0, 0]
        for i in range(0, 5):
            for w in possible_words:
                if w[i] == c:
                    freq[i] += 1
        arr.update({c: freq})
    return arr

def compute_word_score(possible_words, frequencies):
    """Computes a score based off letter frequencies"""
    words = {}
    max_freq = [0, 0, 0, 0, 0]
    for c in frequencies:
        for i in range(0, 5):
            if max_freq[i] < frequencies[c][i]:
                max_freq[i] = frequencies[c][i]
    for w in possible_words:
        score = 1
        for i in range(0, 5):
            c = w[i]
            score *= 1 + (frequencies[c][i] - max_freq[i]) ** 2
        words.update({w: score})
        import numpy
        score += numpy.random.uniform(0, 1)     # this will increase expectation from 2.95 to 3.23, but is technically fairer
    return words

def best_word(possible_words, frequencies):
    """Finds the best word"""
    max_score = 1000000000000000000     # start with a ridiculous score
    best_word = "words"     # start with a random word
    scores = compute_word_score(possible_words, frequencies)
    for w in possible_words:
        if scores[w] < max_score:
            max_score = scores[w]
            best_word = w
    return best_word

def dismiss_initial_tutorial():
    actions.move_by_offset(WINDOW_WIDTH//2, WINDOW_HEIGHT//2).click().perform()
    sleep(2)

def enter_guess_get_result(guess):
    actions.send_keys(guess).perform()
    actions.send_keys(Keys.RETURN).perform()
    actions.pause(2)
    row_elements = driver.find_element(By.CSS_SELECTOR, "game-app").shadow_root \
        .find_element(By.CSS_SELECTOR, f"game-row[letters='{guess.lower()}']").shadow_root \
              .find_elements(By.CSS_SELECTOR, "game-tile") #.find_element(By.CSS_SELECTOR, "game-title[letter='a']")
    evaluation = OrderedDict()
    for idx, (ch, element) in enumerate(zip(guess, row_elements)):
        evaluation[f"{ch}_{idx}"] = element.get_attribute('evaluation')
    return evaluation

def convert_evaluation_dict_to_result(evaluation):
    return "".join([e[0] for e in evaluation.values()])
    

def wordleSolver(possible_words):
    """Prompts you to solve Wordle"""
    print("Welcome to the Wordle Solver!")
    print(f"Let's solve today's ({date.today()}) New York Times Wordle\n")
    
    driver.get(URL)
    dismiss_initial_tutorial()

    game_play = OrderedDict()
    suggestion = best_word(possible_words, get_letter_frequency(possible_words))
    print(f"The suggested starting word is: {suggestion}")
    # diff = (date.today() - date(2021, 6, 19)).days
    # del possible_words[0: diff]
    
    guess = suggestion
    game_play[guess] = enter_guess_get_result(guess)
    print(f"Attempt 1:: {guess} -> {game_play[guess]}\n")
    result = convert_evaluation_dict_to_result(game_play[guess])
    counter = 1
    while result != "ccccc" and counter < 6:
        possible_words = remove_incorrect_words(result, guess, possible_words)
        print(f"Possible Words:: {possible_words}")
        if len(possible_words) == 0:
            break
        suggestion = best_word(possible_words, get_letter_frequency(possible_words))
        print("The next suggested word is:", suggestion)
        guess = suggestion
        game_play[guess] = enter_guess_get_result(guess)
        print(f"Attempt {counter + 1}:: {guess} -> {game_play[guess]}\n")
        result = convert_evaluation_dict_to_result(game_play[guess])
        counter += 1
    if len(possible_words) == 0:
        print("Oh no! You made a mistake entering one of your results. Please try again.")
    elif counter == 6 and result != "ggggg":
        print("Number of guesses exceeded, sorry we failed!")
    else:
        print(f"Congratulations! We solved today's Wordle, \"{guess}\", in {counter} guesses.")


def load_words(file_name):
    with open(file_name) as file:
        words = file.readlines()
    return [word.strip().upper() for word in words]

possible_words = load_words("wordle_words.txt")

options = Options()
options.add_argument("--disable-notifications")
chrome_driver_path = os.getcwd() + "/chromedriver"
driver = webdriver.Chrome(options=options, executable_path=chrome_driver_path)
driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
actions = ActionChains(driver)
driver.implicitly_wait(5)

try:
    wordleSolver(possible_words)
finally:
    sleep(2)
    driver.quit()
