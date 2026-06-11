we want to apply OOP logic to this app
 - we want to have a class Task, class Guideline and other classes. 
 - This class layer should consist of the main logic of the app, for example a Task should be define like in the file @applogics/task_example.py
 - The frontend folder should have 2 layers
   - things related to gradio
   - things that can be used in other frameworks as well, such as react, angular or more. (this thing should be in a seprate folder inside frontend called frontend/designs)
 - Another Sepration of concerns, we need a whole package for our prompts since it has gotton out of hand, for example, in our gradio phase, when we call the prompt for crew ai, we need to do sth like this:
  ex: in file crew.py, we have something like this: """
    Generator that yields stdout log lines from the crew run, then a
    ("RESULT", dict) tuple on success or ("ERROR", str) on failure.

    `subject` is an optional National Curriculum subject (e.g. "Science") that
    steers the Researcher toward curriculum-relevant content.
    """, we don't need it to be here, we can easily create a function in our prompts package that says
        def create_curriculem_based_prompt(subject, otherthings here):
            return """
    Generator that yields stdout log lines from the crew run, then a
    ("RESULT", dict) tuple on success or ("ERROR", str) on failure.

    `subject` is an optional National Curriculum subject (e.g. "Science") that
    steers the Researcher toward curriculum-relevant content.
    """