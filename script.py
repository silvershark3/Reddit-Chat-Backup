import os
import sys
import time
import getpass
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

# This function is for simulating a mouse wheel scrolling.
# For whetever stupid reason Reddit's chat page is setup so
# that it only loads older messages if you scroll using the mouse wheel
# I honestly don't quite understand how this function works, I copied
# it from someone and it does the job.
def wheel_element(element, deltaY = 120, offsetX = 0, offsetY = 0):
  error = element._parent.execute_script("""
    var element = arguments[0];
    var deltaY = arguments[1];
    var box = element.getBoundingClientRect();
    var clientX = box.left + (arguments[2] || box.width / 2);
    var clientY = box.top + (arguments[3] || box.height / 2);
    var target = element.ownerDocument.elementFromPoint(clientX, clientY);

    for (var e = target; e; e = e.parentElement) {
      if (e === element) {
        target.dispatchEvent(new MouseEvent('mouseover', {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY}));
        target.dispatchEvent(new MouseEvent('mousemove', {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY}));
        target.dispatchEvent(new WheelEvent('wheel',     {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY, deltaY: deltaY}));
        return;
      }
    }
    return "Element is not interactable";
    """, element, deltaY, offsetX, offsetY)
  if error:
    raise WebDriverException(error)

#Constants
username = input("Please enter the username of your Reddit account. Not including the 'u/': ")
password = getpass.getpass(prompt="Please enter the password associated with the above account: ")
chat = input("Please enter the name of the chat you would like to backup: ")

waitTime = 25

topOfChat = "//div[text()='This is the start of a beautiful thing. Say something nice, or share a cat fact.']"
tempStopOfChat = "//span[text()='Loading history...']"

#Setup
driver = webdriver.Chrome()
driver.get("https://www.reddit.com/login")

#Login Process
usernameTextBox = driver.find_element_by_id("loginUsername")
passwordTextBox = driver.find_element_by_id("loginPassword")

usernameTextBox.send_keys(username)
passwordTextBox.send_keys(password)

loginButton = driver.find_element_by_xpath("//button[@class='AnimatedForm__submitButton m-full-width']")
loginButton.click()

#Open chat page
driver.get("https://www.reddit.com/chat")

#After the page loads, it takes a little bit of time before the conversations
#actually appear, so this just waits an aonut of time for them to show up

try:
    directsButton = WebDriverWait(driver, waitTime).until(EC.presence_of_element_located(
        (By.XPATH, "//button[@class='_2wJ9IK0tQpgSzeHzXJyT3D ']"))
    )
finally:
    directsButton.click()

#Find specified conversation
chatNamePath = "//span[text()='" + chat + "']"
chatButton = driver.find_element_by_xpath(chatNamePath + "/parent::node()/parent::node()/parent::node()")
chatLink = chatButton.get_attribute("href")

driver.get(chatLink)

#Scroll to the top of the conversation
try:
    username = WebDriverWait(driver, waitTime).until(EC.presence_of_element_located(
        (By.XPATH, "//span[text()='" + username + "']"))
    )
finally:
    while(len(driver.find_elements_by_xpath(topOfChat)) == 0):

        tempStop = driver.find_elements_by_xpath(tempStopOfChat)

        if len(tempStop) == 1:
            actions = ActionChains(driver)
            actions.move_to_element(tempStop[0])
            actions.perform()

            window = driver.find_element_by_xpath("//div[@class='_3GDyz0bgwoWgoxYSYSxXyA _3SalNr9zKm9cow28G6Et8k']")

            wheel_element(window, 50)

    actions = ActionChains(driver)
    actions.move_to_element(driver.find_elements_by_xpath(topOfChat)[0])
    actions.perform()

#Export conversation
container = driver.find_element_by_xpath("//div[@class='_3GDyz0bgwoWgoxYSYSxXyA _3SalNr9zKm9cow28G6Et8k']")

# Gets all subelements of the element

conversation = container.find_elements_by_css_selector("*")

file = open("Chat_archive_" + chat + ".txt", "a")

previousLine = ""

# Since we have all of the subelements, there is often the case where the
# same message is repeated, this makes sure that does not happen

for element in conversation:
    type = element.tag_name

    if type == "a":
        newLine = "\n \n" + element.text + "\n"
        if newLine != previousLine: file.write(newLine)
        previousLine = newLine

    elif type == "div":
        newLine = element.text + "\n"
        if newLine != previousLine: file.write(newLine)
        previousLine = newLine

file.close()
