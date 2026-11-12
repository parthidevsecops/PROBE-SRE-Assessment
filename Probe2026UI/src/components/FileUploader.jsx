import React, { useState } from 'react';

const FileUploader = () => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');

  // Handle file selection
  const handleFileChange = (event) => {
    if (event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  // Handle form submission
  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file) {
      setStatus('Please select a file first.');
      return;
    }

    // FormData is required for sending binary files via multipart/form-data
    const formData = new FormData();
    formData.append('file', file);

    setStatus('Uploading...');

    try {
      const response = await fetch('http://127.0.0', {
        method: 'POST',
        body: formData,
        // Note: Do NOT manually set the Content-Type header when sending FormData.
        // The browser automatically sets it with the required boundary string.
      });

      const data = await response.json();

      if (response.ok) {
        setStatus(`Success: ${data.message}`);
        setFile(null); // Reset input
      } else {
        setStatus(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setStatus('Upload failed. Is the server running?');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>Upload File to Python Directory</h2>
      <form onSubmit={handleUpload}>
        <input type="file" onChange={handleFileChange} />
        <button type="submit" style={{ marginTop: '10px', display: 'block' }}>
          Upload
        </button>
      </form>
      {status && <p style={{ marginTop: '15px', fontWeight: 'bold' }}>{status}</p>}
    </div>
  );
};

export default FileUploader;