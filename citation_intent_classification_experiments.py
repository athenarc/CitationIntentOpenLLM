import pandas as pd
import os
import json
import random
import csv
import numpy as np
from openai import OpenAI
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, classification_report
import subprocess
from pathlib import Path
import string
import warnings
warnings.filterwarnings('ignore') 

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


def write_classification_logs(model_name, reports_file, precision, recall, f1, accuracy, report):
    log_data = (
        f"-------------------------------------------------------------------------\n"
        f"\t\t\t\t\t\t{model_name}\n"
        f"-------------------------------------------------------------------------\n"
        f"Precision: {precision}\tRecall: {recall}\tF1: {f1}\tAccuracy: {accuracy}\n"
        f"-------------------------------------------------------------------------\n"
        f"{report}\n"
        f"-------------------------------------------------------------------------\n"
    )
    with open(reports_file, mode='a', encoding='utf-8') as log_file:
        log_file.write(log_data)


def form_multiple_choice_prompt(class_labels):
    return '\n'.join([f"{letter}) {label}" for letter, label in zip(string.ascii_lowercase, class_labels)])


def add_examples(num_examples, query_template, examples_method, examples_seed, df_train, system_prompt, labels):
    all_example_pairs = []
    random.seed(examples_seed)
    template_qa = "{sentence}\n### Question: Which is the most likely intent for this citation?\n{options}\n### Answer: "
    template_simple = "{sentence} \nClass: "
    multiple_choice = form_multiple_choice_prompt(class_labels) if query_template[0] == '2' else None
    prompt = template_qa if query_template[0] == '2' else template_simple

    if examples_method[0] == '1':
        all_example_pairs = [f"\n{prompt.format(sentence=ex, options=multiple_choice if multiple_choice else '')} {label}\n" for label in labels
            for ex in df_train[df_train['citation_class_label'] == label].sample(num_examples, random_state=examples_seed)['citation_context']]

        random.shuffle(all_example_pairs)
        all_example_pairs = ''.join(all_example_pairs)
        system_prompt[0]['content'] += "\n\n########\n\n# EXAMPLES #\n" + all_example_pairs

    elif examples_method[0] == '2':
        all_example_pairs = [
            [{"role": "user", "content": f"{prompt.format(sentence=ex, options=multiple_choice if multiple_choice else '')}"}, {"role": "assistant", "content": label}]
            for label in labels
            for ex in df_train[df_train['citation_class_label'] == label].sample(num_examples, random_state=examples_seed)['citation_context']
        ]
        random.shuffle(all_example_pairs)
        system_prompt.extend([pair for sublist in all_example_pairs for pair in sublist])

    return system_prompt


def get_predictions(system_prompt, model, sentences, query_template, temperature, multiple_choice=None):
    predicted_classes = []
    template_qa = "{sentence}\n### Question: Which is the most likely intent for this citation? \n{options}\n### Answer:"
    template_simple = "{sentence} \nClass:"

    for sentence in sentences:
        prompt = template_qa if query_template[0] == '2' else template_simple
        message = system_prompt + [{
            "role": "user", 
            "content": prompt.format(sentence=sentence, options=multiple_choice if multiple_choice else "")
        }]
        completion = client.chat.completions.create(
            model=model,
            messages=message,
            max_tokens=15,
            temperature=temperature
        )
        predicted_class = completion.choices[0].message.content.lower().strip()
        predicted_classes.append(predicted_class)
    
    return predicted_classes


def evaluate(true_labels, predicted_labels):
    try:        
        p, r, f1, sup = precision_recall_fscore_support(true_labels, predicted_labels, average='macro')
        acc = round(accuracy_score(true_labels, predicted_labels), 4)
        report = classification_report(true_labels, predicted_labels, output_dict=False)

        return round(p, 4), round(r, 4), round(f1, 4), round(acc, 4), report
    except:
        return None, None, None, None, None


def create_metrics_file(metrics_file_template, metrics_file_path, reports_file_path):
    os.makedirs(metrics_file_path, exist_ok=True)
    os.makedirs(reports_file_path, exist_ok=True)

    metrics_file_path = os.path.join(metrics_file_path, metrics_file_template)

    with open(metrics_file_path, mode='w+', encoding='utf-8') as fl:
        fl.write("Model,Precision,Recall,F1-Score,Accuracy\n")
    
    return metrics_file_path


def clean_labels(df, labels, column_name='predicted_classes'):
    letter_to_label = {letter: label for letter, label in zip(string.ascii_lowercase, labels)}
    df['non_cleaned_prediction'] = df[column_name].copy()
    
    def check_and_replace(text):
        stripped_text = text.strip().lower().rstrip(')')
        
        if stripped_text in letter_to_label:
            return letter_to_label[stripped_text]

        count_labels = {label: text.lower().count(label.lower()) for label in labels}
        if sum(count_labels.values()) == 1:
            return next(label for label, count in count_labels.items() if count == 1)
        
        return np.nan

    df[column_name] = df[column_name].apply(check_and_replace)
    
    return df


def run_analysis(df_test, system_prompt, model_path, model_name, class_labels, test_sentences, metrics_file, reports_file, model_output_file_template, model_output_file_path, query_template, temperature):
    multiple_choice = form_multiple_choice_prompt(class_labels) if query_template[0] == '2' else None

    df_test['predicted_classes'] = get_predictions(
        system_prompt=system_prompt, 
        model=model_path, 
        sentences=test_sentences, 
        query_template=query_template, 
        temperature=temperature, 
        multiple_choice=multiple_choice
    )
    df_test_cleaned = clean_labels(df=df_test, labels=class_labels)

    test_true_classes = df_test_cleaned["citation_class_label"].to_list()
    test_pred_classes = df_test_cleaned["predicted_classes"].to_list()

    p, r, f1, acc, report = evaluate(true_labels=test_true_classes, predicted_labels=test_pred_classes)

    os.makedirs(model_output_file_path, exist_ok=True)
    model_output_file_path = os.path.join(model_output_file_path, model_output_file_template)
    df_test_cleaned.to_csv(model_output_file_path, index=False)

    fieldnames = ['Model', 'Precision', 'Recall', 'F1-Score', 'Accuracy']
    formatted_row = {
        'Model': model_name,
        'Precision': p,
        'Recall': r,
        'F1-Score': f1,
        'Accuracy': acc
    }

    with open(metrics_file, mode='a', encoding='utf-8') as fl:
        csv_writer = csv.DictWriter(fl, fieldnames=fieldnames, quoting=csv.QUOTE_NONE)
        csv_writer.writerow(formatted_row)

    write_classification_logs(model_name, reports_file, p, r, f1, acc, report)


if __name__ == "__main__":
    subprocess.run(["lms", "server", "start"])
    subprocess.run(["lms", "unload", "--all"])

    experiment_cfg_path = os.path.join('experimental-configs', 'experiments_cfg.json')
    experiment_cfg = json.loads(Path(experiment_cfg_path).read_text())

    methods = experiment_cfg['methods']
    num_examples = experiment_cfg['number_of_examples']
    examples_seed = experiment_cfg['examples_seed']
    datasets = experiment_cfg['datasets']
    system_prompts = experiment_cfg['system_prompts']
    class_labels = experiment_cfg['class_labels']
    examples_methods = experiment_cfg['examples_methods']
    query_templates = experiment_cfg['query_templates']
    temperature = experiment_cfg['temperature']
    bit_precision = experiment_cfg['bit_precision']
    run_id = experiment_cfg['run_id']
    finetuned = experiment_cfg['finetuned']
    system_prompt = []

    if finetuned:
        models_cfg_path = os.path.join('experimental-configs', f"models.{bit_precision}.ft.json")
    else:
        models_cfg_path = os.path.join('experimental-configs', f'models.{bit_precision}.json')
    models_cfg = json.loads(Path(models_cfg_path).read_text())
    
    system_prompts_cfg_path = os.path.join('experimental-configs', 'system_prompts.json')
    system_prompts_cfg = json.loads(Path(system_prompts_cfg_path).read_text())

    datasets_path = os.path.join('datasets', 'formatted')
    
    for dataset in datasets:

        df_test = pd.read_csv(os.path.join(datasets_path, dataset, "test.csv"))
        df_train = pd.read_csv(os.path.join(datasets_path, dataset, "train.csv"))

        test_sentences = df_test["citation_context"].to_list()
        test_true_classes = df_test["citation_class_label"].to_list()

        class_labels = class_labels[dataset]

        for method in methods:
            for sp in system_prompts:
                prompt_id = f"{dataset}{sp}"

                system_prompt = [{
                    "role": "system", 
                    "content": system_prompts_cfg[prompt_id]
                }]
                if method != 'zero-shot':
                    for em in examples_methods:
                        for qt in query_templates:
                            system_prompt = add_examples(
                                num_examples=num_examples[method],
                                query_template=qt,
                                examples_method=em,
                                examples_seed=examples_seed, 
                                df_train=df_train, 
                                system_prompt=system_prompt, 
                                labels=class_labels
                            )

                            for temp in temperature:
                                metrics_file_path = os.path.join('results', dataset, run_id, method, "metrics")
                                reports_file_path = os.path.join(metrics_file_path, "classification_reports")
                                metrics_file_template = f"_metrics_{dataset}_{method}_SP{sp}_QT{qt[0]}_EM{em[0]}_T{temp}_{bit_precision}.csv"

                                if not os.path.exists(os.path.join(metrics_file_path, metrics_file_template)):
                                    metrics_file = create_metrics_file(metrics_file_template, metrics_file_path, reports_file_path)
                                else:
                                    metrics_file = os.path.join(metrics_file_path, metrics_file_template)
                                reports_file = os.path.join(reports_file_path, metrics_file_template.replace('csv', 'log'))

                                for model_name, model_metadata in models_cfg.items():
                                    model_path = model_metadata['path']
                                    model_context_length = model_metadata['context_length']

                                    model_output_file_path = os.path.join('results', dataset, run_id, method, f"SP{sp}", f"QT{qt[0]}", f"EM{em[0]}", f"T{temp}")
                                    model_output_file_template = f"{model_name}_{dataset}_{method}_SP{sp}_QT{qt[0]}_EM{em[0]}_T{temp}_{bit_precision}.csv"

                                    subprocess.run(["lms", "load", model_path, "--gpu", "max", "--exact", "--context-length", model_context_length])
                                    run_analysis(
                                        df_test=df_test,
                                        system_prompt=system_prompt,
                                        model_path=model_path,
                                        model_name=model_name,
                                        class_labels=class_labels,
                                        test_sentences=test_sentences,
                                        model_output_file_template=model_output_file_template, 
                                        model_output_file_path=model_output_file_path,
                                        metrics_file=metrics_file,
                                        reports_file=reports_file,
                                        query_template=qt,
                                        temperature=temp
                                    )
                                    subprocess.run(["lms", "unload", "--all"])
                else:
                    for qt in query_templates:
                        for temp in temperature:
                            metrics_file_path = os.path.join('results', dataset, run_id, method, "metrics")
                            reports_file_path = os.path.join(metrics_file_path, "classification_reports")
                            metrics_file_template = f"_metrics_{dataset}_{method}_SP{sp}_QT{qt[0]}_T{temp}_{bit_precision}.csv"

                            if not os.path.exists(os.path.join(metrics_file_path, metrics_file_template)):
                                metrics_file = create_metrics_file(metrics_file_template, metrics_file_path, reports_file_path)
                            else:
                                metrics_file = os.path.join(metrics_file_path, metrics_file_template)
                            reports_file = os.path.join(reports_file_path, metrics_file_template.replace('csv', 'log'))


                            for model_name, model_metadata in models_cfg.items():
                                model_path = model_metadata['path']
                                model_context_length = model_metadata['context_length']

                                model_output_file_path = os.path.join('results', dataset, run_id, method, f"SP{sp}", f"QT{qt[0]}", f"T{temp}")
                                model_output_file_template = f"{model_name}_{dataset}_{method}_SP{sp}_QT{qt[0]}_T{temp}_{bit_precision}.csv"

                                subprocess.run(["lms", "load", model_path, "--gpu", "max", "--exact", "--context-length", model_context_length])
                                run_analysis(
                                    df_test=df_test,
                                    system_prompt=system_prompt,
                                    model_path=model_path,
                                    model_name=model_name,
                                    class_labels=class_labels,
                                    test_sentences=test_sentences,
                                    model_output_file_template=model_output_file_template, 
                                    model_output_file_path=model_output_file_path,
                                    metrics_file=metrics_file,
                                    reports_file=reports_file,
                                    query_template=qt,
                                    temperature=temp
                                )
                                subprocess.run(["lms", "unload", "--all"])

    subprocess.run(["lms", "server", "stop"])