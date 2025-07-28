import React, { useState } from 'react';
import { Upload, Input } from 'antd';
import { CloudUploadOutlined, FileTextOutlined } from '@ant-design/icons';
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

  const draggerProps = {
    name: 'file',
    multiple: false,
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
            <FileTextOutlined style={{ marginRight: 8 }} />
            <span>{fileList[0].name}</span>
          </div>
        ) : (
          <>
            <p className="upload-icon"><CloudUploadOutlined /></p>
            <p className="upload-text">将文件拖拽至此，或点击选择</p>
            <p className="upload-text-small">支持 PDF, DOCX, TXT</p>
          </>
        )}
      </Dragger>
    </section>
  );
};

export default KnowledgeSourceForm;