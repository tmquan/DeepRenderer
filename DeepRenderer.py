#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Tran Minh Quan, quantm@unist.ac.kr
import os, sys, argparse, glob, cv2

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


# Misc. libraries
from six.moves import map, zip, range
from natsort import natsorted 

# Array and image processing toolboxes
import numpy as np 
import skimage
import skimage.io
import skimage.transform

###################################################################################################
from tensorpack import *
from tensorpack.dataflow import dataset
from tensorpack.utils.gpu import get_nr_gpu
from tensorpack.tfutils import optimizer, gradproc
from tensorpack.tfutils.summary import add_moving_summary, add_param_summary
from tensorpack.tfutils.scope_utils import auto_reuse_variable_scope
from tensorpack.utils import logger


###################################################################################################
EPOCH_SIZE = 100
NB_FILTERS = 16	  # channel size

DIMX  = 256
DIMY  = 256
DIMZ  = 256
DIMC  = 1
####################################################################################################
class ImageDataFlow(RNGDataFlow):
	def __init__(self, image_path, style_path, size, dtype='float32', isTrain=False, isValid=False):
		self.dtype      	= dtype
		self.image_path   	= image_path
		self.style_path   	= style_path
		self._size      	= size
		self.isTrain    	= isTrain
		self.isValid    	= isValid

	def size(self):
		return self._size

	def reset_state(self):
		self.rng = get_rng(self)

	def get_data(self, shuffle=True):
		#
		# Read and store into pairs of images and labels
		#
		images = glob.glob(self.image_path + '/*.*')
		styles = glob.glob(self.style_path + '/*.*')

		if self._size==None:
			self._size = len(images)

		from natsort import natsorted
		images = natsorted(images)
		styles = natsorted(styles)


		#
		# Pick the image over size 
		#
		for k in range(self._size):
			#
			# Pick randomly a tuple of training instance
			#
			rand_image = np.random.randint(0, len(images))
			rand_style = np.random.randint(0, len(styles))

			if self.isTrain:
			# Rotate and resample volume
			else:
				# Adjust via callback 
				# Rotate 360 degree
				pass
####################################################################################################
def get_data(image_path, style_path, size=EPOCH_SIZE):
	ds_train = ImageDataFlow(image_path,
							 style_path, 
							 size, 
							 isTrain=True
							 )

	ds_valid = ImageDataFlow(image_path,
							 style_path, 
							 size, 
							 isValid=True
							 )

	ds_train.reset_state()
	ds_valid.reset_state() 

	return ds_train, ds_valid

			
####################################################################################################
class Model(ModelDesc):
	def _get_inputs(self):
		pass

	def _build_graph(self, inputs):
		pass

	def _get_optimizer(self):
		pass

###################################################################################################
def apply(model_path, image_path, style_path):
	pass

###################################################################################################
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--gpu', help='comma separated list of GPU(s) to use.')
	parser.add_argument('--load', help='load model')
	parser.add_argument('--apply', action='store_true')
	parser.add_argument('--image', help='data')
	parser.add_argument('--style',  help='path to the style. ')
	parser.add_argument('--vgg19', help='load model', default="data/vgg19.npz")
	parser.add_argument('--output', help='directory for saving predicted high-res image', default=".", type=str)
	args = parser.parse_args()

	if args.gpu:
		os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

	if args.apply:
		apply(args.load, args.image, args.style)
	else:
		# Set the logger directory
		logger.auto_set_dir()

		nr_tower = max(get_nr_gpu(), 1)
		ds_train = QueueInput(get_data(args.data))
		model = Model()

		if args.load:
            session_init = SaverRestore(args.load)
        else:
            assert os.path.isfile(args.vgg19)
            param_dict = dict(np.load(args.vgg19))
            param_dict = {'VGG19/' + name: value for name, value in six.iteritems(param_dict)}
            session_init = DictRestore(param_dict)

		
			# Set up configuration
			config = TrainConfig(
				model           =   model, 
				dataflow        =   ds_train,
				callbacks       =   [
					PeriodicTrigger(ModelSaver(), every_k_epochs=50),
					PeriodicTrigger(VisualizeRunner(ds_valid), every_k_epochs=5),
					#PeriodicTrigger(InferenceRunner(ds_valid, [ScalarStats('loss_membr')]), every_k_epochs=5),
					ScheduledHyperParamSetter('learning_rate', [(0, 2e-4), (100, 1e-4), (200, 1e-5), (300, 1e-6)], interp='linear')
					#ScheduledHyperParamSetter('learning_rate', [(30, 6e-6), (45, 1e-6), (60, 8e-7)]),
	            	#HumanHyperParamSetter('learning_rate'),
					],
				max_epoch       =   500, 
				session_init    =   session_init,
				nr_tower        =   max(get_nr_gpu(), 1)
				)
		
			# Train the model
			SyncMultiGPUTrainer(config).train()

	
	
		