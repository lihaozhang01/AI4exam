import React, { useState } from 'react';
import { Upload, Input, Button } from 'antd';
import { CloudUploadOutlined, FileTextOutlined, DeleteOutlined } from '@ant-design/icons';
import './Forms.css';

const { Dragger } = Upload;
const { TextArea } = Input;

const KnowledgeSourceForm = ({ source, onSourceChange }) => {
  const { sourceText, fileList } = source;
  const [isDragOver, setIsDragOver] = useState(false);

  const handleTextChange = (e) => {
    onSourceChange({ ...source, sourceText: e.target.value });
  };

  const handleFileChange = (info) => {
    let newFileList = [...info.fileList];
    newFileList = newFileList.slice(-1); // Only keep the last file
    onSourceChange({ ...source, fileList: newFileList });
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation(); // Stop propagation to prevent opening file dialog
    onSourceChange({ ...source, fileList: [] });
  };

  const draggerProps = {
    name: 'file',
    multiple: false,
    accept: '.doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.txt,text/plain,.md,text/markdown',
    fileList,
    onChange: handleFileChange,
    beforeUpload: () => false, // Prevent auto-upload
    showUploadList: false, // We show file info manually
    onDrop: () => setIsDragOver(false),
  };

  return (
    <section className="knowledge-source-section">
      <h3 className="section-title"><span className="title-decorator"></span>知识源</h3>
      <p className="section-subtitle">请粘贴文本或上传文件作为出题依据。</p>
      
      <TextArea
        rows={8}
        value={sourceText}
        onChange={handleTextChange}
        placeholder="在此处粘贴文本知识源..."
        className="source-textarea"
      />

      <div className="divider-text">或</div>

      <Dragger 
        {...draggerProps} 
        className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
        onDragEnter={() => setIsDragOver(true)}
        onDragLeave={() => setIsDragOver(false)}
      >
        {fileList.length > 0 ? (
          <div className="file-info">
            <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <span className="file-name">{fileList[0].name}</span>
            <Button 
              type="text" 
              icon={<DeleteOutlined />} 
              onClick={handleRemoveFile} 
              className="remove-file-btn"
            />
          </div>
        ) : (
          <>
            <p className="upload-icon"><CloudUploadOutlined /></p>
            <p className="upload-text">将文件拖拽至此，或点击选择</p>
            <p className="upload-text-small">
              目前仅支持DOCX，TXT，Markdown等文本文件，
              <br />
              其他文本文件可修改后缀上传。
            </p>
          </>
        )}
      </Dragger>
    </section>
  );
};

export default KnowledgeSourceForm;