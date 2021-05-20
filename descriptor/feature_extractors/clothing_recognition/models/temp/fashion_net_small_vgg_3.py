# import the necessary packages
from keras.models import Model
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import MaxPooling2D
from keras.layers.core import Activation
from keras.layers.core import Dropout
from keras.layers.core import Lambda
from keras.layers.core import Dense
from keras.layers import Flatten
from keras.layers import Input
import tensorflow as tf


class FashionNet:
    @staticmethod
    def build_category_branch(inputs, num_categories, final_act="softmax",
                              chan_dim=-1, convert_to_grayscale=True):

        # Use a lambda layer to convert the 3 channel input to a
        # grayscale representation
        if convert_to_grayscale:
            x = Lambda(lambda c: tf.image.rgb_to_grayscale(c))(inputs)
        else:
            x = inputs

        # CONV => RELU => POOL
        x = Conv2D(32, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(3, 3))(x)
        x = Dropout(0.25)(x)

        # (CONV => RELU) * 2 => POOL
        x = Conv2D(64, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(64, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Dropout(0.25)(x)

        # (CONV => RELU) * 2 => POOL
        x = Conv2D(128, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(128, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Dropout(0.25)(x)

        # (CONV => RELU) * 3 => POOL
        x = Conv2D(256, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(256, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(256, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Dropout(0.25)(x)

        # define a branch of output layers for the number of different
        # clothing categories (i.e., shirts, jeans, dresses, etc.)
        x = Flatten()(x)
        x = Dense(1024)(x)
        x = Activation("relu")(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)
        x = Dense(num_categories)(x)
        x = Activation(final_act, name="category_output")(x)

        # return the category prediction sub-network
        return x


    @staticmethod
    def build_color_branch(inputs, num_colors, final_act="softmax",
                           chan_dim=-1):

        # CONV => RELU => POOL
        x = Conv2D(32, (3, 3), padding="same")(inputs)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(3, 3))(x)
        x = Dropout(0.25)(x)

        # (CONV => RELU) * 2 => POOL
        x = Conv2D(64, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(64, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Dropout(0.25)(x)

        # (CONV => RELU) * 2 => POOL
        x = Conv2D(128, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(128, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Dropout(0.25)(x)

        # (CONV => RELU) * 3 => POOL
        x = Conv2D(256, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(256, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = Conv2D(256, (3, 3), padding="same")(x)
        x = Activation("relu")(x)
        x = BatchNormalization(axis=chan_dim)(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Dropout(0.25)(x)

        # define a branch of output layers for the number of different
        # clothing categories (i.e., shirts, jeans, dresses, etc.)
        x = Flatten()(x)
        x = Dense(1024)(x)
        x = Activation("relu")(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)
        x = Dense(num_colors)(x)
        x = Activation(final_act, name="color_output")(x)

        # return the color prediction sub-network
        return x

    @staticmethod
    def build(width, height, num_categories=None, num_colors=None,
              final_act="softmax", convert_to_grayscale=True):

        # Initialize input shape and channel dimension (using channels last ordering)
        input_shape = (height, width, 3)
        chan_dim = -1

        # Construct both "category" and "color" sub-networks
        inputs = Input(shape=input_shape)
        if num_categories is not None:
            category_branch = FashionNet.build_category_branch(inputs, num_categories, final_act=final_act,
                                                               chan_dim=chan_dim,
                                                               convert_to_grayscale=convert_to_grayscale)
        if num_colors is not None:
            color_branch = FashionNet.build_color_branch(inputs,
                                                         num_colors, final_act=final_act, chan_dim=chan_dim)

        model = None
        if num_categories is not None and num_colors is not None:

            # Create model using the batch of images as input and
            # two separate outputs, one for the clothing category
            # branch and another for the color branch, respectively
            model = Model(
                inputs=inputs,
                outputs=[category_branch, color_branch],
                name='fashion_net')
        elif num_categories is not None and num_colors is None:

            # Create model using only category output
            model = Model(
                inputs=inputs,
                outputs=category_branch,
                name='fashion_net'
            )
        elif num_categories is None and num_colors is not None:

            # Create model using only color output
            model = Model(
                inputs=inputs,
                outputs=color_branch,
                name='fashion_net'
            )

        # Return the constructed network architecture
        return model
