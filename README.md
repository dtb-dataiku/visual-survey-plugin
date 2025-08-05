# visual-survey-plugin
_A Dataiku plugin to create survey web apps_

**Overview**: This plugin builds a survey Dash web app from questions stored in a Dataiku dataset and stores responses as JSON files in a Dataiku managed folder.

## Setup
### Question Dataset
This data should have the following schema:
- A column for **question type**<sup>1</sup> with the following valid options: _**single_choice**_, _**multi_choice**_, _**rank**_, or _**text**_.
- A column containing a **short name**<sup>2</sup> for the question (ex. Question 1). Each question must have a unique name as this will be used to identify the question.
- A column containing the **question**<sup>3</sup>.
- A column listing the possible **options**<sup>4</sup> for _single__ or _multi_choice_ question types. The option should be separated by **"|"**.
- A column for a **default**<sup>5</sup> option. If provided, this default option must be included in the list of options.
- A column to indicate if a **response**<sup>6</sup> is required.
<img width="954" height="263" alt="Screenshot 2025-08-05 at 2 12 43 PM" src="https://github.com/user-attachments/assets/721b85da-9d70-4adb-aff5-e454c5f1b99d" />

### App Settings
The web app settings require a name, description, selection of question dataset, mapping of columns from question dataset, selection response folder, and whether to anonymize the responses.
<img width="814" height="735" alt="Screenshot 2025-08-05 at 2 12 13 PM" src="https://github.com/user-attachments/assets/c3b69bdc-ed5f-419d-9798-dd3b553b383e" />
