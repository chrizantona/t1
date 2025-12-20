interface IdeEditorProps {
  code: string
  onChange: (code: string) => void
  language: string
}

function IdeEditor({ code, onChange, language }: IdeEditorProps) {
  return (
    <textarea
      value={code}
      onChange={(e) => onChange(e.target.value)}
      placeholder={`Напишите код на ${language}...`}
      style={{
        flex: 1,
        width: '100%',
        padding: '20px',
        fontFamily: 'Monaco, Menlo, "Courier New", monospace',
        fontSize: '14px',
        lineHeight: '1.5',
        background: '#1e1e1e',
        color: '#d4d4d4',
        border: 'none',
        outline: 'none',
        resize: 'none',
      }}
    />
  )
}

export default IdeEditor


// пидормот
