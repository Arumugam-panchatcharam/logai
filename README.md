# RDK_One3B
AI-Powered Fault Detection, Prediction and Auto-Healing for Home connectivity


## Installation

### Quick Install

```shell

# Check out rdk_one3b code repo from Github
git clone https://github.com/Arumugam-panchatcharam/logai.git
cd logai

# [Optional] Create virtual environment
python3 -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
pip install nltk
python -m nltk.downloader punkt_tab

# Start rdk_one3b service
export PYTHONPATH='.'  # make sure to add current root to PYTHONPATH
python3 logai/gui/application.py # Run local plotly dash server.

```


## Reference
    * [Salesforce LogAI](https://github.com/salesforce/logai): A Library for Log Analytics and Intelligence
## License
[BSD 3-Clause License](LICENSE.txt)
