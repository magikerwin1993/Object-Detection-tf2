import tensorflow as tf

def resize(img, bboxes, h_dst, w_dst):
    """resize without fixed aspect ratio"""
    w_src = tf.cast(tf.shape(img)[1], tf.float32)
    h_src = tf.cast(tf.shape(img)[0], tf.float32)
    
    # resize image
    img_dst = tf.image.resize(img, [h_dst, w_dst], antialias=True)
    
    # refine bboxes
    scale_w = w_dst / w_src
    scale_h = h_dst / h_src
    bboxes_dst = bboxes * [scale_w, scale_h, scale_w, scale_h]
    return img_dst, bboxes_dst

def resize_with_fixed_AR(img, bboxes, h_dst, w_dst):
    """resize with fixed aspect ratio"""
    w_src = tf.cast(tf.shape(img)[1], tf.float32)
    h_src = tf.cast(tf.shape(img)[0], tf.float32)
    
    # resize image
    if h_dst > h_src * (w_dst / w_src):
        scale = (w_dst / w_src)
    else:
        scale = (h_dst / h_src)
    h_tmp = tf.cast(scale * h_src, tf.int32)
    w_tmp = tf.cast(scale * w_src, tf.int32)
    img_dst = tf.image.resize(img, [h_tmp, w_tmp], antialias=True)
    
    # padding
    pad_t = tf.cast((h_dst - h_tmp) / 2, tf.int32)
    pad_b = (h_dst - h_tmp) - pad_t
    pad_l = tf.cast((w_dst - w_tmp) / 2, tf.int32)
    pad_r = (w_dst - w_tmp) - pad_l
    img_dst = tf.pad(img_dst, [[pad_t, pad_b], [pad_l, pad_r], [0,0]], "CONSTANT")
    
    # refine bboxes
    bboxes_dst = bboxes * scale + [pad_l, pad_t, pad_l, pad_t]
    return img_dst, bboxes_dst

def preprocess(img, bboxes, img_dims):
    """pre-process for data pipeline"""
    # img, bboxes = resize(img, bboxes, h_dst=img_dims[0], w_dst=img_dims[1])
    img, bboxes = resize_with_fixed_AR(img, bboxes, h_dst=img_dims[0], w_dst=img_dims[1])
    return img, bboxes

def _parse_tfrecord(img_dims):
    """create parser(mapping) for tf.dataset"""
    def parse_tfrecord(tfrecord):
        feature = {
            'image/name':   tf.io.FixedLenFeature([], tf.string),
            'image/encode': tf.io.FixedLenFeature([], tf.string),
            'label/bboxes': tf.io.FixedLenFeature([], tf.string),
        }
        example = tf.io.parse_single_example(tfrecord, feature)
        img = tf.image.decode_jpeg(example['image/encode'], channels=3)
        bboxes = tf.io.decode_raw(example['label/bboxes'], tf.float32)
        bboxes = tf.reshape(bboxes, [-1, 4])
        bboxes = tf.pad(bboxes, [[0, 100], [0, 0]], "CONSTANT")[:100, :]
        return preprocess(img, bboxes, img_dims)
    return parse_tfrecord

def load_tfrecord_dataset(path_tfrecord, img_dims=[100, 100], batch_size=16,
                          shuffle=True, buffer_size=10240):
    """load dataset from tfrecord"""    
    raw_dataset = tf.data.TFRecordDataset(path_tfrecord)
    raw_dataset = raw_dataset.repeat()
    if shuffle:
        raw_dataset = raw_dataset.shuffle(buffer_size=buffer_size)

    parser = _parse_tfrecord(img_dims)

    dataset = raw_dataset.map(parser, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    dataset = dataset.batch(batch_size, drop_remainder=True)
    dataset = dataset.prefetch(
        buffer_size=tf.data.experimental.AUTOTUNE)

    return dataset