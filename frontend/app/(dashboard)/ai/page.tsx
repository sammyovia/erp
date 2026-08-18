'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { formatDate, getStatusColor } from '@/lib/utils';
import { FileUp, Check, X, Loader2, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AIPage() {
  const [file, setFile] = useState<File | null>(null);
  const [candidateId, setCandidateId] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['ai-extractions'],
    queryFn: () => aiApi.listExtractions(),
  });

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => aiApi.analyzeCV(formData.get('file') as File, formData.get('candidate_id') as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-extractions'] });
      toast.success('CV analyzed successfully!');
      setFile(null);
      setCandidateId('');
      setIsUploading(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to analyze CV');
      setIsUploading(false);
    },
  });

  const confirmMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => aiApi.confirmExtraction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-extractions'] });
      toast.success('Extraction confirmed!');
    },
    onError: () => {
      toast.error('Failed to confirm extraction');
    },
  });

  const handleUpload = () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    if (candidateId) formData.append('candidate_id', candidateId);
    uploadMutation.mutate(formData as any);
  };

  const extractions = data?.data?.results || [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
        <p className="text-gray-600 mt-1">Upload CVs and extract candidate data using AI</p>
      </div>

      <Card className="mb-6">
        <h3 className="text-lg font-semibold mb-4">Upload CV for Analysis</h3>
        <div className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              id="cv-upload"
              accept=".pdf,.txt,.doc,.docx"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  setFile(e.target.files[0]);
                }
              }}
            />
            <label htmlFor="cv-upload" className="cursor-pointer">
              <FileUp className="h-12 w-12 mx-auto text-gray-400 mb-3" />
              {file ? (
                <p className="text-sm text-blue-600 font-medium">{file.name}</p>
              ) : (
                <p className="text-sm text-gray-500">Click to upload or drag and drop</p>
              )}
              <p className="text-xs text-gray-400 mt-1">PDF, TXT, DOC (max 10MB)</p>
            </label>
          </div>

          <Input
            label="Candidate ID (optional)"
            placeholder="Enter candidate ID if updating existing"
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            fullWidth
          />

          <Button 
            onClick={handleUpload} 
            disabled={!file || isUploading}
            fullWidth
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Analyze CV
              </>
            )}
          </Button>
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Extraction History</h3>
        {isLoading ? (
          <div className="text-center py-8">Loading extractions...</div>
        ) : extractions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto text-gray-300 mb-3" />
            <p>No AI extractions yet</p>
            <p className="text-sm">Upload a CV to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {extractions.map((extraction: any) => (
              <div key={extraction.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(extraction.status)}`}>
                        {extraction.status_display}
                      </span>
                      <span className="text-sm text-gray-500">Model: {extraction.model_used}</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                      <p><span className="text-gray-500">Name:</span> {extraction.extracted_data?.full_name || 'N/A'}</p>
                      <p><span className="text-gray-500">Email:</span> {extraction.extracted_data?.email || 'N/A'}</p>
                      <p><span className="text-gray-500">Experience:</span> {extraction.extracted_data?.years_experience || 0} years</p>
                      <p><span className="text-gray-500">Skills:</span> {extraction.extracted_data?.skills?.join(', ') || 'N/A'}</p>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">{formatDate(extraction.created_at)}</p>
                  </div>
                  {extraction.status === 'pending_confirmation' && (
                    <div className="flex gap-2">
                      <button
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        onClick={() => {
                          if (confirm('Confirm this extraction and create candidate?')) {
                            confirmMutation.mutate({ 
                              id: extraction.id, 
                              data: { action: 'confirm' } 
                            });
                          }
                        }}
                        disabled={confirmMutation.isPending}
                      >
                        <Check className="h-5 w-5" />
                      </button>
                      <button
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        onClick={() => {
                          if (confirm('Reject this extraction?')) {
                            confirmMutation.mutate({ 
                              id: extraction.id, 
                              data: { action: 'reject' } 
                            });
                          }
                        }}
                        disabled={confirmMutation.isPending}
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}