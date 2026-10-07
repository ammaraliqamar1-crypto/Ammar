'use strict';
// Built-in demo connector so the app is usable before the ASG server is linked.
function createDemoConnector() {
  const inquiries = [
    { id: 'INQ-001', client: 'Demo Contractor', project: 'Villa Glass Balustrade', status: 'Under Estimation' },
    { id: 'INQ-002', client: 'Sample Developer', project: 'Curtain Wall Tower B', status: 'Quoted' },
  ];
  const tools = [
    {
      name: 'list_inquiries',
      description: 'List inquiries/RFQs, optionally filtered by status.',
      parameters: { type: 'object', properties: { status: { type: 'string' } } },
      risk: 'read',
      run: async ({ status } = {}) => inquiries.filter((i) => !status || i.status === status),
    },
    {
      name: 'update_inquiry_status',
      description: 'Change the status of an inquiry.',
      parameters: {
        type: 'object',
        properties: { id: { type: 'string' }, status: { type: 'string' } },
        required: ['id', 'status'],
      },
      risk: 'write',
      run: async ({ id, status }) => {
        const i = inquiries.find((x) => x.id === id);
        if (!i) throw new Error(`Inquiry ${id} not found`);
        i.status = status;
        return i;
      },
    },
  ];
  return { id: 'demo', loadTools: async () => tools, ping: async () => true };
}
module.exports = { createDemoConnector };
