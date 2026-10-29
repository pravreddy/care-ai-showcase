import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Button, Grid, Chip, IconButton, Alert,
  CircularProgress, Card, CardContent, CardActions, Divider,
  ToggleButton, ToggleButtonGroup,
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import FilterListIcon from '@mui/icons-material/FilterList';
import { templateService } from '../../services/api';

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'NDA', label: 'NDA' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'INVOICE', label: 'Invoice' },
  { value: 'PROPOSAL', label: 'Proposal' },
  { value: 'AGREEMENT', label: 'Agreement' },
  { value: 'OTHER', label: 'Other' },
];

export default function TemplatesPage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('');

  useEffect(() => { loadTemplates(); }, [category]); // eslint-disable-line

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const data = await templateService.list(category || undefined);
      setTemplates(data.results || data || []);
    } catch (err) {
      setError('Failed to load templates.');
    } finally {
      setLoading(false);
    }
  };

  const handleUseTemplate = async (template) => {
    const title = prompt('Document title:', `${template.name} — Copy`);
    if (!title) return;
    try {
      const result = await templateService.useTemplate(template.id, title);
      const docId = result.document?.id;
      if (docId) {
        navigate(`/documents/${docId}`);
      } else {
        alert(result.message || 'Document created!');
        loadTemplates();
      }
    } catch (err) {
      setError('Failed to create document from template.');
    }
  };

  const handleDelete = async (template) => {
    if (!window.confirm(`Delete template "${template.name}"?`)) return;
    try {
      await templateService.delete(template.id);
      loadTemplates();
    } catch (err) {
      setError('Failed to delete template.');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>Template Library</Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Box sx={{ mb: 3 }}>
        <ToggleButtonGroup
          value={category}
          exclusive
          onChange={(e, val) => setCategory(val ?? '')}
          size="small"
        >
          {CATEGORIES.map((c) => (
            <ToggleButton key={c.value} value={c.value}>{c.label}</ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      {templates.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No templates yet. Save a document as a template from the document detail page.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {templates.map((t) => (
            <Grid item xs={12} sm={6} md={4} key={t.id}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                    <DescriptionIcon color="primary" />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>{t.name}</Typography>
                      {t.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          {t.description}
                        </Typography>
                      )}
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1.5 }}>
                    <Chip label={t.category} size="small" variant="outlined" />
                    {t.is_system_template && <Chip label="System" size="small" color="primary" />}
                    {t.is_premium && <Chip label="Premium" size="small" color="secondary" />}
                    {t.fields_config?.length > 0 && (
                      <Chip label={`${t.fields_config.length} fields`} size="small" color="info" variant="outlined" />
                    )}
                  </Box>

                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
                    {t.page_count ? `${t.page_count} pages` : ''}{t.page_count && t.use_count > 0 ? ' · ' : ''}
                    {t.use_count > 0 ? `Used ${t.use_count} times` : ''}
                  </Typography>
                </CardContent>

                <Divider />

                <CardActions sx={{ justifyContent: 'space-between', px: 2 }}>
                  <Button size="small" startIcon={<ContentCopyIcon />} onClick={() => handleUseTemplate(t)}>
                    Use Template
                  </Button>
                  {!t.is_system_template && (
                    <IconButton size="small" color="error" onClick={() => handleDelete(t)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
