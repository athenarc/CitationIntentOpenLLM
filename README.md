# Citation Intent Open LLMs

Supplementary material for paper "Can LLMs Predict Citation Intent? An Experimental Analysis of In-context Learning and Fine-tuning on Open LLMs".


## Experiential evaluation

### Current top results for each model

<table>
<tr><th> SciCite </th><th> ACL-ARC </th></tr>
<tr><td>

| Rank | Model               | F1-Score |
| ---- | ------------------- | -------- |
|    1 | Qwen 2.5 - 14B      |    78.33 |
|    2 | Gemma 2 - 27B       |    77.86 |
|    3 | Mistral Nemo - 12B  |    77.39 |
|    4 | Gemma 2 - 9B        |    75.12 |
|    5 | Phi 3 Medium - 14B  |    74.67 |
|    6 | LLaMA 3 - 8B        |    74.39 |
|    7 | Qwen 2 - 7B         |    72.89 |
|    8 | LLaMA 3.1 - 8B      |    72.46 |
|    9 | Gemma 2 - 2B        |    68.79 |
|   10 | Phi 3.5 Mini - 3.8B |    68.25 |
|   11 | LLaMA 3.2 - 3B      |    67.99 |
|   12 | LLaMA 3.2 - 1B      |    45.44 |

</td><td>

| Rank | Model               | F1-Score |
| ---- | ------------------- | -------- |
|    1 | Qwen 2.5 - 14B      |    63.68 |
|    2 | Gemma 2 - 27B       |    58.95 |
|    3 | Gemma 2 - 9B        |    57.19 |
|    4 | Qwen 2 - 7B         |    51.26 |
|    5 | LLaMA 3.1 - 8B      |    48.45 |
|    6 | Mistral Nemo - 12B  |    48.11 |
|    7 | Phi 3.5 Mini - 3.8B |    43.74 |
|    8 | Phi 3 Medium - 14B  |    43.46 |
|    9 | Gemma 2 - 2B        |    40.96 |
|   10 | LLaMA 3.2 - 3B      |    40.07 |
|   11 | LLaMA 3 - 8B        |    38.06 |
|   12 | LLaMA 3.2 - 1B      |    24.60 |

</td></tr> </table>

### Instructions

#### Prerequisites
> *Support for additional inference providers is under development*
- [LM Studio](https://lmstudio.ai/) (version 0.3.10 or higher)
- LM Studio CLI ([lms](https://github.com/lmstudio-ai/lms))

#### Setup and Configuration
1. Configure Models
    > *The default configuration includes all models used in the paper*
    - Open `experimental-configs/models.q8.json`
    - Select your target models and specify their context lengths
      
2. Model Installation - Choose one of these methods to download the required models:
    - Use the LM Studio UI
    - Run the command: `lms get <model-name>`
    
3. Experiment Configuration
    > *In the default configuration, all parameters are selected*
    - Open `experimental-configs\experimens-cfg.json`
    - Select your desired evaluation parameters

#### Running the Evaluation
1. Navigate to the root directory
2. Execute the evaluation script:

```bash
python citation_intent_classification_experiments.py
```

## Fine-tuning

### Prerequisites
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) (commit: [`24c7842`](https://github.com/hiyouga/LLaMA-Factory/tree/24c78429489809873a1269a735ea5421340b32a2))
- All LLaMA-Factory dependencies installed

> LLaMA-Factory is very quick to iterate, so later versions may not be totally compatible with the current config files - although the changes are usually very minor).

> The training parameters in `llama-factory-configs/{dataset}/training_args.yaml` are platform-independent and can be used with any Supervised Fine-tuning system.

### Dataset Preparation
1. Copy Dataset Files
    - Source locations:
      ```
      datasets/aplaca_format_scicite/
      └── scicite_train_alpaca.json
      └── scicite_dev_alpaca.json
      
      datasets/alpaca_format/acl-arc/
      └── aclarc_train_alpaca.json
      └── aclarc_dev_alpaca.json
      ```
     - Destination: `LLaMA-Factory/data/`
2. Update Dataset Information
     - Add the following to `LLaMA-Factory/data/dataset_info.json`:  
       ```json
       "scicite": {
           "file_name": "scicite_train_alpaca.json",
           "columns": {
               "prompt": "instruction",
               "query": "input",
               "response": "output",
               "system": "system"
           }
       },
       "scicite-calibration": {
           "file_name": "scicite_dev_alpaca.json",
           "columns": {
               "prompt": "instruction",
               "query": "input",
               "response": "output",
               "system": "system"
           }
       },
       "aclarc": {
           "file_name": "aclarc_train_alpaca.json",
           "columns": {
               "prompt": "instruction",
               "query": "input",
               "response": "output",
               "system": "system"
           }
       },
       "aclarc-calibration": {
           "file_name": "aclarc_dev_alpaca.json",
           "columns": {
             "prompt": "instruction",
             "query": "input",
             "response": "output",
             "system": "system"
           }
       }
       ```

### Configuration Setup
1. Create a new directory: `LLaMA-Factory/config/`
2. Copy all configuration files from `llama-factory-configs/` to the new directory

### Training
> For this step consult the LLaMA-Factory docs as well.

Choose one of these methods:
1. GUI Method
    - Launch LLaMA Board interface
    - Load your configuration
    - Start training run
2. CLI Method
    ```bash
    llamafactory-cli train path/to/training_args.yaml
    ```

### Model Export
Export the model using the dev set of the selected dataset (either `scicite_dev_alpaca.json` or `aclarc_dev_alpaca.json`) as a calibration dataset

### Optional: GGUF Conversion
To create GGUF model versions, install [llama.cpp](https://github.com/ggml-org/llama.cpp) and run:
```bash
python convert_hf_to_gguf_update.py
```
