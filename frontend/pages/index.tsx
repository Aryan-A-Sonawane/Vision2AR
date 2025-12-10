import React from 'react';
import { useRouter } from 'next/router';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';

export default function Home() {
  const router = useRouter();

  const features = [
    {
      title: 'Adaptive Diagnosis',
      description: 'Smart questioning system that quickly identifies your laptop issue with minimal steps.',
      icon: '🔍',
    },
    {
      title: 'AR Guided Repair',
      description: 'Step-by-step visual overlays show exactly where to work on your device.',
      icon: '🔧',
    },
    {
      title: 'Multi-Source Knowledge',
      description: 'Browse 800+ repair guides from OEM manuals, iFixit, and community.',
      icon: '📚',
      onClick: () => router.push('/guides')
    },
    {
      title: 'Safety First',
      description: 'Clear risk warnings and rollback instructions for every repair step.',
      icon: '🛡️',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-neutral-200">
      {/* Header */}
      <header className="border-b border-neutral-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-neutral-900 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">AR</span>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-neutral-900">Laptop Troubleshooter</h1>
                <p className="text-xs text-neutral-500">AI-Powered Repair Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => router.push('/guides')}
              >
                Browse Guides
              </Button>
              <Button variant="ghost" size="sm">
                About
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-5xl font-bold text-neutral-900 mb-6 text-balance">
            Fix Your Laptop with
            <span className="block mt-2 bg-gradient-to-r from-neutral-800 to-neutral-600 bg-clip-text text-transparent">
              AR-Guided Precision
            </span>
          </h2>
          <p className="text-xl text-neutral-600 mb-8 max-w-2xl mx-auto text-balance">
            Diagnose issues through smart questions, then follow step-by-step visual guides 
            with augmented reality overlays. No guesswork, just results.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Button 
              size="lg" 
              onClick={() => router.push('/diagnose')}
              className="shadow-lg"
            >
              Start Diagnosis →
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              onClick={() => router.push('/guides')}
              className="shadow-md"
            >
              📚 Browse Repair Guides
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              onClick={() => router.push('/devices')}
            >
              Browse Devices
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              hover
              onClick={feature.onClick}
              className={`animate-slide-up ${feature.onClick ? 'cursor-pointer' : ''}`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <CardContent>
                <div className="text-4xl mb-4">{feature.icon}</div>
                <CardTitle className="mb-2">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Repair Guides CTA */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 mb-16 text-white">
          <div className="max-w-3xl mx-auto text-center">
            <h3 className="text-3xl font-bold mb-4">
              800+ Repair Guides Available
            </h3>
            <p className="text-lg text-blue-100 mb-6">
              Browse step-by-step repair instructions for Lenovo, Dell, HP, Asus, and more. 
              From battery replacements to motherboard repairs.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Button 
                size="lg"
                onClick={() => router.push('/guides')}
                className="bg-white text-blue-600 hover:bg-blue-50"
              >
                Browse All Guides
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => router.push('/guides/create')}
                className="border-2 border-white text-white hover:bg-white/10"
              >
                Contribute Your Guide
              </Button>
            </div>
            <div className="mt-6 flex items-center justify-center gap-8 text-sm text-blue-100">
              <span>✓ OEM Manuals</span>
              <span>✓ iFixit Integration</span>
              <span>✓ Community Verified</span>
            </div>
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-white rounded-2xl border border-neutral-200 shadow-medium p-8 mb-16">
          <h3 className="text-2xl font-bold text-neutral-900 mb-8 text-center">
            How It Works
          </h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-neutral-900 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h4 className="font-semibold text-neutral-900 mb-2">Describe the Problem</h4>
              <p className="text-neutral-600 text-sm">
                Answer a few targeted questions about your laptop symptoms. Our AI narrows down the cause quickly.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-neutral-900 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h4 className="font-semibold text-neutral-900 mb-2">Get Diagnosis</h4>
              <p className="text-neutral-600 text-sm">
                Receive a confident diagnosis with root cause explanation and required tools list.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-neutral-900 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h4 className="font-semibold text-neutral-900 mb-2">Follow AR Guide</h4>
              <p className="text-neutral-600 text-sm">
                Step-by-step visual overlays show exactly where screws, connectors, and parts are located.
              </p>
            </div>
          </div>
        </div>

        {/* Supported Brands */}
        <div className="text-center">
          <h3 className="text-lg font-medium text-neutral-700 mb-6">Supported Brands - Click to View Repair Guides</h3>
          <div className="flex items-center justify-center gap-12 flex-wrap">
            {['Lenovo', 'Dell', 'HP'].map((brand) => (
              <button
                key={brand}
                onClick={() => router.push(`/guides/${brand.toLowerCase()}`)}
                className="text-2xl font-bold text-neutral-400 hover:text-neutral-900 transition-colors cursor-pointer"
              >
                {brand}
              </button>
            ))}
          </div>
          <div className="mt-6">
            <Button 
              variant="outline"
              onClick={() => router.push('/guides')}
            >
              View All Brands & Models →
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-200 bg-white mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-sm text-neutral-500">
            <p>© 2025 AR Laptop Troubleshooter. All rights reserved.</p>
            <p className="mt-2">Built with safety and accuracy in mind.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
