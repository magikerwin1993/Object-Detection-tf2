import yaml
from absl import logging
from modules.dataset import load_tfrecord_dataset

def load_yaml(yaml_path):
    """load yaml file"""
    with open(yaml_path, 'r') as f:
        loaded = yaml.load(f, Loader=yaml.Loader)
    return loaded

def load_dataset(cfg, shuffle=True, buffer_size=10240):
    """load dataset"""
    logging.info('load dataset from {}'.format(cfg['dataset_path']))
    dataset = load_tfrecord_dataset(
        path_tfrecord=cfg['dataset_path'],
        img_dims=[224, 224],
        batch_size=16,
        shuffle=shuffle,
        buffer_size=buffer_size)
    return dataset