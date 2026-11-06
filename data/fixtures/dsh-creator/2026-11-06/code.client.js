return {
  apply(ctx) {
    const slots = ctx.get('slots');
    if (!slots) return;
    const h = React.createElement;
    function Workbench() {
      const [title, setTitle] = React.useState('Everything is a plugin');
      const [text, setText] = React.useState('');
      const [colorA, setColorA] = React.useState('#6554e8');
      const [colorB, setColorB] = React.useState('#20c6b7');
      const fieldStyle = { display: 'grid', gap: '6px' };
      const inputStyle = { boxSizing: 'border-box', width: '100%', padding: '9px', border: '1px solid #cbd0da', borderRadius: '8px', font: 'inherit' };
      return h('section', { 'aria-label': 'Poster design workbench', style: { fontFamily: 'system-ui, sans-serif', padding: '16px', color: '#202331', display: 'grid', gap: '16px' } },
        h('div', { 'aria-label': 'Poster preview', style: { minHeight: '360px', padding: 'clamp(24px, 6%, 64px)', boxSizing: 'border-box', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'center', overflowWrap: 'anywhere', backgroundColor: colorA, backgroundImage: 'radial-gradient(ellipse at 15% 20%, ' + colorB + ' 0%, transparent 65%), radial-gradient(ellipse at 90% 85%, ' + colorB + ' 0%, transparent 60%), linear-gradient(135deg, ' + colorA + ', ' + colorB + ')' } },
          h('div', { style: { padding: '24px', borderRadius: '12px', background: 'rgba(255,255,255,0.88)' } },
            h('h1', { style: { margin: 0, fontSize: 'clamp(32px, 6vw, 64px)', lineHeight: 1.05, letterSpacing: '-0.04em', whiteSpace: 'pre-wrap' } }, title),
            text ? h('p', { style: { margin: '20px 0 0', fontSize: '18px', lineHeight: 1.5, whiteSpace: 'pre-wrap' } }, text) : null)),
        h('div', { style: { display: 'grid', gap: '12px' } },
          h('label', { style: fieldStyle }, 'Title', h('input', { type: 'text', value: title, onChange: e => setTitle(e.target.value), style: inputStyle })),
          h('label', { style: fieldStyle }, 'Text', h('textarea', { value: text, rows: 3, onChange: e => setText(e.target.value), style: inputStyle })),
          h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '24px' } },
            h('label', { style: fieldStyle }, 'Color 1', h('input', { type: 'color', value: colorA, onChange: e => setColorA(e.target.value) })),
            h('label', { style: fieldStyle }, 'Color 2', h('input', { type: 'color', value: colorB, onChange: e => setColorB(e.target.value) })))));
    }
    ctx.effect(() => slots.inject('tool.view.cordis', () => slots.register({ name: 'tool.view.cordis', key: 'self' }, Workbench)));
  }
};
