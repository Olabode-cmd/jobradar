export interface RoleTemplate {
  id: string;
  label: string;
  role: string;
  keywords: string[];
}

export const ROLE_TEMPLATES: readonly RoleTemplate[] = [
  {
    id: 'software-engineer',
    label: 'Software engineer',
    role: 'Software engineer',
    keywords: ['software engineer', 'developer', 'backend', 'frontend', 'full stack'],
  },
  {
    id: 'designer',
    label: 'Designer',
    role: 'Product designer',
    keywords: ['product designer', 'ux', 'ui', 'figma', 'design systems'],
  },
  {
    id: 'marketing',
    label: 'Marketing',
    role: 'Marketing manager',
    keywords: ['marketing', 'growth', 'content', 'seo', 'lifecycle'],
  },
  {
    id: 'data-analyst',
    label: 'Data analyst',
    role: 'Data analyst',
    keywords: ['data analyst', 'sql', 'python', 'tableau', 'analytics'],
  },
];
