# import threading
# from selenium import webdriver

# def run_browser(link):
#     # Create a new instance of the browser
#     driver = webdriver.Firefox()  # You can use other browser drivers as well
#     driver.get(link)
#     # Perform your automation tasks here
#     # ...

#     # Close the browser when done
#     # driver.quit()

# # Create two threads, each running a browser instance
# thread1 = threading.Thread(target=run_browser, args=("https://www.google.com",))
# thread2 = threading.Thread(target=run_browser, args=("https://www.facebook.com",))


# # Start the threads
# thread1.start()
# thread2.start()

# # Wait for both threads to finish
# thread1.join()
# thread2.join()

import concurrent.futures
import time
from selenium import webdriver

def another_function(link):
    driver = webdriver.Firefox()  # You can use other browser drivers as well
    driver.get("https://www.hotmail.com")
    time.sleep(3)
    print(f"Inside of {link} done ")
    driver.quit()



def process_link(link):
    # Create a new instance of the browser
    driver = webdriver.Firefox()  # You can use other browser drivers as well
    driver.get(link)
    
    another_function(link)
    # Perform your automation tasks here
    time.sleep(2)
    print(f"Link - {link} completed.")

    # Close the browser when done
    driver.quit()

# List of links to process
link_list = ["https://www.google.com", "https://www.facebook.com",
             "https://www.reddit.com", "https://www.bored.com",
             "https://www.9gag.com", "https://www.gmail.com",
             "https://www.123musiq.com", "https://www.datacamp.com"]  # Add all your links here

# Maximum number of concurrent threads
max_threads = 3

# Create a thread pool executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_threads)

# Submit tasks for each link in the list
futures = [executor.submit(process_link, link) for link in link_list]

# Wait for all tasks to complete
concurrent.futures.wait(futures)
