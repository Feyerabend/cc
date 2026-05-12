import tensorflow as tf
import numpy as np
from PIL import Image
import os

class StyleGANDigit:
    """StyleGAN-inspired architecture for high-quality digit generation"""
    
    def __init__(self, latent_dim=512, style_dim=512, lr=0.001):
        self.latent_dim = latent_dim
        self.style_dim = style_dim
        self.img_shape = (28, 28, 1)
        self.lr = lr
        
        # Build networks
        self.mapping_network = self.build_mapping_network()
        self.generator = self.build_stylegan_generator()
        self.discriminator = self.build_stylegan_discriminator()
        
        # Optimizers
        self.gen_optimizer = tf.keras.optimizers.Adam(lr, beta_1=0.0, beta_2=0.99)
        self.disc_optimizer = tf.keras.optimizers.Adam(lr, beta_1=0.0, beta_2=0.99)
        
    def build_mapping_network(self):
        """Mapping network to transform latent codes to style codes"""
        z_input = tf.keras.layers.Input(shape=(self.latent_dim,))
        
        x = z_input
        for _ in range(8):  # 8 fully connected layers
            x = tf.keras.layers.Dense(self.style_dim, activation='relu')(x)
            x = tf.keras.layers.LayerNormalization()(x)
        
        return tf.keras.Model(z_input, x, name='mapping_network')
    
    def adaptive_instance_norm(self, x, style):
        """Adaptive Instance Normalization as a layer"""
        class AdaIN(tf.keras.layers.Layer):
            def __init__(self, **kwargs):
                super(AdaIN, self).__init__(**kwargs)
                
            def build(self, input_shape):
                x_shape, style_shape = input_shape
                self.style_scale = tf.keras.layers.Dense(x_shape[-1], activation='linear')
                self.style_bias = tf.keras.layers.Dense(x_shape[-1], activation='linear')
                super(AdaIN, self).build(input_shape)
                
            def call(self, inputs):
                x, style = inputs
                # Instance normalization
                mean, variance = tf.nn.moments(x, axes=[1, 2], keepdims=True)
                x_norm = (x - mean) / tf.sqrt(variance + 1e-8)
                
                # Style modulation
                scale = self.style_scale(style)
                bias = self.style_bias(style)
                
                scale = tf.reshape(scale, [-1, 1, 1, tf.shape(x)[-1]])
                bias = tf.reshape(bias, [-1, 1, 1, tf.shape(x)[-1]])
                
                return scale * x_norm + bias
        
        return AdaIN()([x, style])
    
    def style_conv_block(self, x, style, filters, kernel_size=3, upsample=False):
        """Stylized convolution block"""
        if upsample:
            x = tf.keras.layers.UpSampling2D()(x)
        
        x = tf.keras.layers.Conv2D(filters, kernel_size, padding='same')(x)
        x = self.adaptive_instance_norm(x, style)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        return x
    
    def build_stylegan_generator(self):
        """StyleGAN-inspired generator"""
        style_input = tf.keras.layers.Input(shape=(self.style_dim,))
        
        # Create a custom layer for the learned constant - FIXED VERSION
        class LearnedConstant(tf.keras.layers.Layer):
            def __init__(self, **kwargs):
                super(LearnedConstant, self).__init__(**kwargs)
                
            def build(self, input_shape):
                self.const = self.add_weight(
                    name='learned_constant',
                    shape=(1, 4, 4, 512),
                    initializer='random_normal',
                    trainable=True
                )
                super(LearnedConstant, self).build(input_shape)
                
            def call(self, inputs):
                # Use tf.shape within call method, not during model construction
                batch_size = tf.shape(inputs)[0]
                return tf.tile(self.const, [batch_size, 1, 1, 1])
        
        x = LearnedConstant()(style_input)
        
        # Apply initial style
        x = self.adaptive_instance_norm(x, style_input)
        
        # Progressive upsampling with style injection
        x = self.style_conv_block(x, style_input, 256, upsample=True)  # 8x8
        x = self.style_conv_block(x, style_input, 128, upsample=True)  # 16x16
        x = self.style_conv_block(x, style_input, 64, upsample=False)  # 16x16
        
        # Final upsampling to 28x28 (closest to 32x32)
        x = tf.keras.layers.UpSampling2D(size=(2, 2), interpolation='bilinear')(x)  # 32x32
        x = tf.keras.layers.Conv2D(32, 3, padding='same')(x)
        x = self.adaptive_instance_norm(x, style_input)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        # Crop to 28x28
        x = tf.keras.layers.Cropping2D(cropping=2)(x)  # 28x28
        
        # Final output
        x = tf.keras.layers.Conv2D(1, 1, padding='same', activation='tanh')(x)
        
        return tf.keras.Model(style_input, x, name='stylegan_generator')
    
    def minibatch_stddev(self, x):
        """Minibatch standard deviation for discriminator"""
        class MinibatchStddev(tf.keras.layers.Layer):
            def __init__(self, group_size=4, **kwargs):
                super(MinibatchStddev, self).__init__(**kwargs)
                self.group_size = group_size
                
            def call(self, x):
                batch_size = tf.shape(x)[0]
                group_size = tf.minimum(self.group_size, batch_size)
                s = tf.shape(x)
                y = tf.reshape(x, [group_size, -1, s[1], s[2], s[3]])
                y = tf.cast(y, tf.float32)
                y -= tf.reduce_mean(y, axis=0, keepdims=True)
                y = tf.reduce_mean(tf.square(y), axis=0)
                y = tf.sqrt(y + 1e-8)
                y = tf.reduce_mean(y, axis=[1, 2, 3], keepdims=True)
                y = tf.tile(y, [group_size, s[1], s[2], 1])
                return tf.concat([x, y], axis=-1)
        
        return MinibatchStddev()(x)
    
    def build_stylegan_discriminator(self):
        """StyleGAN-inspired discriminator with progressive structure"""
        img_input = tf.keras.layers.Input(shape=self.img_shape)
        
        x = img_input
        
        # Progressive downsampling
        x = tf.keras.layers.Conv2D(64, 3, padding='same')(x)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        x = tf.keras.layers.Conv2D(128, 3, strides=2, padding='same')(x)  # 14x14
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        x = tf.keras.layers.Conv2D(256, 3, strides=2, padding='same')(x)  # 7x7
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        x = tf.keras.layers.Conv2D(512, 3, padding='same')(x)
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        # Minibatch standard deviation
        x = self.minibatch_stddev(x)
        
        x = tf.keras.layers.Conv2D(512, 3, padding='same')(x)
        x = tf.keras.layers.LeakyReLU(0.2)(x)
        
        x = tf.keras.layers.Flatten()(x)
        x = tf.keras.layers.Dense(1)(x)
        
        return tf.keras.Model(img_input, x, name='stylegan_discriminator')
    
    def r1_penalty(self, real_images):
        """R1 regularization penalty"""
        with tf.GradientTape() as tape:
            tape.watch(real_images)
            real_pred = self.discriminator(real_images, training=True)
            real_loss = tf.reduce_sum(real_pred)
        
        gradients = tape.gradient(real_loss, real_images)
        penalty = tf.reduce_mean(tf.reduce_sum(tf.square(gradients), axis=[1, 2, 3]))
        return penalty
    
    @tf.function
    def train_step(self, real_images):
        batch_size = tf.shape(real_images)[0]
        
        # Generate random latent codes and map to style space
        z = tf.random.normal([batch_size, self.latent_dim])
        style = self.mapping_network(z, training=True)
        
        # Train discriminator
        with tf.GradientTape() as disc_tape:
            fake_images = self.generator(style, training=True)
            
            real_pred = self.discriminator(real_images, training=True)
            fake_pred = self.discriminator(fake_images, training=True)
            
            # Wasserstein loss
            disc_loss = tf.reduce_mean(fake_pred) - tf.reduce_mean(real_pred)
            
            # R1 regularization
            r1_reg = self.r1_penalty(real_images)
            disc_loss += 10.0 * r1_reg
        
        disc_gradients = disc_tape.gradient(disc_loss, self.discriminator.trainable_variables)
        self.disc_optimizer.apply_gradients(zip(disc_gradients, self.discriminator.trainable_variables))
        
        # Train generator and mapping network
        with tf.GradientTape() as gen_tape:
            z = tf.random.normal([batch_size, self.latent_dim])
            style = self.mapping_network(z, training=True)
            fake_images = self.generator(style, training=True)
            fake_pred = self.discriminator(fake_images, training=True)
            
            gen_loss = -tf.reduce_mean(fake_pred)
        
        gen_variables = self.generator.trainable_variables + self.mapping_network.trainable_variables
        gen_gradients = gen_tape.gradient(gen_loss, gen_variables)
        self.gen_optimizer.apply_gradients(zip(gen_gradients, gen_variables))
        
        return gen_loss, disc_loss
    
    def generate_images(self, num_images=16, truncation_psi=0.7):
        """Generate images with truncation trick"""
        z = tf.random.normal([num_images, self.latent_dim])
        
        # Apply truncation trick
        if truncation_psi < 1.0:
            # Compute average style vector (would need to be precomputed in practice)
            z_avg = tf.zeros([1, self.latent_dim])
            style_avg = self.mapping_network(z_avg, training=False)
            
            styles = self.mapping_network(z, training=False)
            styles = style_avg + truncation_psi * (styles - style_avg)
        else:
            styles = self.mapping_network(z, training=False)
            
        return self.generator(styles, training=False)

def load_sevens_data():
    """Load and preprocess MNIST digit 7 data"""
    (x_train, y_train), (_, _) = tf.keras.datasets.mnist.load_data()
    seven_indices = np.where(y_train == 7)[0]
    x_train_sevens = x_train[seven_indices]
    
    # Normalize to [-1, 1]
    x_train_sevens = (x_train_sevens.astype('float32') - 127.5) / 127.5
    x_train_sevens = x_train_sevens.reshape(-1, 28, 28, 1)
    
    return x_train_sevens

def save_generated_images(images, filename, grid_size=(4, 4)):
    """Save generated images as a grid"""
    images = (images * 127.5 + 127.5).astype(np.uint8)
    grid_rows, grid_cols = grid_size
    img_size = 28
    
    grid_img = Image.new('L', (grid_cols * img_size, grid_rows * img_size))
    
    for i in range(min(grid_rows * grid_cols, len(images))):
        row = i // grid_cols
        col = i % grid_cols
        img = Image.fromarray(images[i, :, :, 0], mode='L')
        grid_img.paste(img, (col * img_size, row * img_size))
    
    grid_img.save(filename)
    print(f'Saved generated images as {filename}')

def train_stylegan():
    """Main training function for StyleGAN"""
    # Load data
    x_train_sevens = load_sevens_data()
    
    # Create dataset
    batch_size = 32  # Smaller batch size for StyleGAN
    dataset = tf.data.Dataset.from_tensor_slices(x_train_sevens)
    dataset = dataset.shuffle(buffer_size=10000).batch(batch_size, drop_remainder=True)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)
    
    # Initialize model
    stylegan = StyleGANDigit()
    
    # Create directories
    os.makedirs('stylegan_images', exist_ok=True)
    os.makedirs('checkpoints_stylegan', exist_ok=True)
    
    # Checkpointing
    checkpoint = tf.train.Checkpoint(
        mapping_network=stylegan.mapping_network,
        generator=stylegan.generator,
        discriminator=stylegan.discriminator,
        gen_optimizer=stylegan.gen_optimizer,
        disc_optimizer=stylegan.disc_optimizer
    )
    checkpoint_manager = tf.train.CheckpointManager(
        checkpoint, './checkpoints_stylegan', max_to_keep=5
    )
    
    # Training loop
    epochs = 40
    save_interval = 10
    
    with open('stylegan_training_log.txt', 'w') as log_file:
        for epoch in range(epochs):
            gen_losses = []
            disc_losses = []
            
            for batch in dataset:
                gen_loss, disc_loss = stylegan.train_step(batch)
                gen_losses.append(gen_loss)
                disc_losses.append(disc_loss)
            
            # Log progress
            gen_loss_avg = np.mean(gen_losses)
            disc_loss_avg = np.mean(disc_losses)
            
            print(f'Epoch {epoch+1}/{epochs} - Gen Loss: {gen_loss_avg:.4f}, Disc Loss: {disc_loss_avg:.4f}')
            log_file.write(f'Epoch {epoch+1}, Gen Loss: {gen_loss_avg:.4f}, Disc Loss: {disc_loss_avg:.4f}\n')
            
            # Save images periodically
            if (epoch + 1) % save_interval == 0:
                generated_images = stylegan.generate_images(16, truncation_psi=0.7)
                save_generated_images(
                    generated_images.numpy(), 
                    f'stylegan_images/stylegan_epoch_{epoch+1}.png'
                )
                
                # Save checkpoint
                checkpoint_manager.save()
                print(f'Saved checkpoint and images for epoch {epoch+1}')

if __name__ == "__main__":
    train_stylegan()