import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Loader2,
  FileType
} from 'lucide-react';
import { uploadDocument, deleteDocument } from '../services/api';

export default function UploadPage({ documents = [], onRefreshDocuments }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    const validExtensions = ['.pdf', '.pptx', '.ppt', '.docx', '.txt'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExt) {
      setErrorMessage(`Unsupported file format. Please upload PDF, PPTX, DOCX, or TXT.`);
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMessage(`File exceeds 25MB maximum upload limit.`);
      return;
    }

    setErrorMessage(null);
    setStatusMessage(null);
    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await uploadDocument(file, (progress) => {
        setUploadProgress(progress);
      });

      setStatusMessage(`Successfully processed "${file.name}"! Indexed into ${response.total_chunks} semantic chunks.`);
      if (onRefreshDocuments) onRefreshDocuments();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to process document.';
      setErrorMessage(`Upload error: ${msg}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to remove "${filename}" from the study portal?`)) {
      return;
    }
    try {
      await deleteDocument(docId);
      setStatusMessage(`Deleted "${filename}" and its vector embeddings.`);
      if (onRefreshDocuments) onRefreshDocuments();
    } catch (err) {
      setErrorMessage(`Delete error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Upload Zone */}
      <div className="card">
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Upload Course Materials
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
          Supported: <strong>PDF</strong> (page-by-page), <strong>PPTX/PPT</strong> (slide-by-slide), <strong>DOCX</strong>, and <strong>TXT</strong> notes.
        </p>

        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
          onClick={() => !uploading && fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${isDragging ? 'var(--primary)' : '#cbd5e1'}`,
            borderRadius: '12px',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            background: isDragging ? 'var(--primary-light)' : '#f8fafc',
            cursor: uploading ? 'wait' : 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFiles(e.target.files)}
            accept=".pdf,.docx,.pptx,.ppt,.txt"
            style={{ display: 'none' }}
          />

          <div style={{
            width: '56px', height: '56px', borderRadius: '50%',
            background: '#eef2ff', color: 'var(--primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1rem auto'
          }}>
            {uploading ? <Loader2 size={28} className="animate-spin" /> : <UploadCloud size={28} />}
          </div>

          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
            {uploading ? 'Parsing and embedding document...' : 'Click or drag files here to upload'}
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            PDF, PPTX, DOCX, TXT up to 25MB
          </p>

          {uploading && (
            <div style={{ marginTop: '1.5rem', maxWidth: '350px', marginLeft: 'auto', marginRight: 'auto' }}>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress > 0 ? uploadProgress : 60}%`, background: 'var(--primary)' }}
                />
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.5rem' }}>
                {uploadProgress > 0 ? `Uploading (${uploadProgress}%)` : 'Extracting semantic chunks and embeddings...'}
              </span>
            </div>
          )}
        </div>

        {/* Notifications */}
        {statusMessage && (
          <div style={{
            marginTop: '1.25rem', padding: '0.85rem 1rem', borderRadius: '8px',
            background: 'var(--success-light)', border: '1px solid #bbf7d0',
            color: '#166534', display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.875rem'
          }}>
            <CheckCircle2 size={18} />
            <span>{statusMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div style={{
            marginTop: '1.25rem', padding: '0.85rem 1rem', borderRadius: '8px',
            background: 'var(--danger-light)', border: '1px solid #fecaca',
            color: '#991b1b', display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.875rem'
          }}>
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* Indexed Documents Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Indexed Course Materials</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Materials currently stored in ChromaDB and available for RAG question answering.
            </p>
          </div>
          <span className="badge badge-primary">
            {documents.length} File{documents.length !== 1 ? 's' : ''}
          </span>
        </div>

        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
            <FileType size={40} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
            <p style={{ fontSize: '0.925rem' }}>No documents uploaded yet.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Document</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Type</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Size</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Sections / Pages</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Date Uploaded</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}>
                    <td style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <FileText size={18} color="var(--primary)" />
                        <span>{doc.filename}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700,
                        background: doc.source_type === 'pdf' ? '#fee2e2' : doc.source_type === 'pptx' ? '#ffedd5' : '#e0e7ff',
                        color: doc.source_type === 'pdf' ? '#b91c1c' : doc.source_type === 'pptx' ? '#c2410c' : '#3730a3',
                        textTransform: 'uppercase'
                      }}>
                        {doc.source_type}
                      </span>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>
                      {doc.total_sections} {doc.source_type === 'pptx' ? 'slides' : 'pages/sections'}
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {doc.created_at?.split('.')[0] || 'Recently'}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="btn btn-danger"
                        style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                        title="Delete Document"
                      >
                        <Trash2 size={14} /> Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
