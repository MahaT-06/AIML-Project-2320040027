import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (LSTM, Dense, Embedding, Input, 
                                     Attention, Dropout, Conv1D, 
                                     BatchNormalization, GlobalAveragePooling1D)
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from tensorflow.keras.preprocessing.sequence import pad_sequences
import py3Dmol

# Define amino acids and mapping
amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
aa_to_int = {aa: i + 1 for i, aa in enumerate(amino_acids)}  # Start indexing from 1

def encode_sequence(sequence, max_len=150):
    """Encodes and pads amino acid sequence into integer representation."""
    encoded = [aa_to_int.get(aa, 0) for aa in sequence if aa in aa_to_int]
    return pad_sequences([encoded], maxlen=max_len, padding='post')

# Complex Model Architecture
def build_complex_model(input_length):
    inputs = Input(shape=(input_length,))
    
    # Embedding layer to process input sequence
    x = Embedding(input_dim=len(amino_acids) + 1, output_dim=128, input_length=input_length)(inputs)
    x = Dropout(0.3)(x)
    
    # CNN layers to capture spatial dependencies
    x = Conv1D(64, kernel_size=3, activation='relu', padding='same')(x)
    x = BatchNormalization()(x)
    x = Conv1D(128, kernel_size=5, activation='relu', padding='same')(x)
    x = BatchNormalization()(x)
    
    # LSTM layers for sequence processing
    x = LSTM(256, return_sequences=True)(x)
    x = Dropout(0.3)(x)
    
    # Self-Attention mechanism
    attention = Attention()([x, x])
    x = tf.keras.layers.concatenate([x, attention])
    x = LSTM(128)(x)
    x = Dropout(0.3)(x)
    
    # Global pooling for feature extraction
    x = GlobalAveragePooling1D()(x)
    
    # Fully connected layers for final output
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.4)(x)
    outputs = Dense(3, activation='linear')(x)  # 3D coordinates as output
    
    # Build and compile model
    model = Model(inputs, outputs)
    model.compile(optimizer='adam', loss='mse')
    return model

def visualize_3d_structure(prediction):
    """Visualize 3D coordinates using Py3Dmol in Streamlit."""
    view = py3Dmol.view(width=400, height=400)
    
    # Generate the PDB formatted data from prediction coordinates
    pdb_data = "MODEL\n"
    for i, (x, y, z) in enumerate(prediction):
        pdb_data += f"ATOM  {i+1:5d}  CA  ALA A{i+1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C\n"
    pdb_data += "ENDMDL\n"
    
    # Load the PDB structure
    view.addModel(pdb_data, 'pdb')
    view.setStyle({'cartoon': {'color': 'spectrum'}})
    view.zoomTo()
    
    return view

# Streamlit UI
st.title("Advanced Protein 3D Structure Prediction and Visualization")
st.write("Input an amino acid sequence to predict its 3D structure and visualize it.")

# User input
sequence = st.text_input("Amino Acid Sequence (max 150 characters):", "ACDEFGHIKLMNPQRSTVWY")
if len(sequence) > 150:
    st.error("Sequence too long. Please enter up to 150 characters.")

if st.button("Predict and Visualize Structure"):
    if all(aa in amino_acids for aa in sequence):
        # Encode and reshape input sequence
        encoded_seq = encode_sequence(sequence, max_len=150)
        
        # Build and predict with the complex model
        model = build_complex_model(input_length=150)
        predictions = model.predict(encoded_seq).reshape(-1, 3)  # Reshape for visualization
        
        # Display predicted 3D coordinates in a table
        st.write("Predicted 3D Coordinates (x, y, z):")
        st.write(predictions)
        
        # Visualize in 3D using Py3Dmol
        view = visualize_3d_structure(predictions)
        view.show()
        
        # Additional bioinformatics analysis
        analyzed_seq = ProteinAnalysis(sequence)
        st.write("Molecular Weight:", analyzed_seq.molecular_weight())
        st.write("Aromaticity:", analyzed_seq.aromaticity())
        st.write("Instability Index:", analyzed_seq.instability_index())
        st.write("Isoelectric Point:", analyzed_seq.isoelectric_point())
        st.write("Secondary Structure Fraction (Helix, Turn, Sheet):", analyzed_seq.secondary_structure_fraction())
        
        # Sequence composition for further insights
        st.write("Amino Acid Composition:", analyzed_seq.get_amino_acids_percent())
    else:
        st.error("Invalid characters in sequence. Please use valid amino acid symbols only.")