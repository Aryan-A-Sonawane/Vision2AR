import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface Device {
  id: string;
  brand: string;
  model: string;
  image?: string;
}

export default function DevicesPage() {
  const router = useRouter();
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);

  const brands = [
    { id: 'lenovo', name: 'Lenovo', count: 2 },
    { id: 'dell', name: 'Dell', count: 2 },
    { id: 'hp', name: 'HP', count: 2 },
  ];

  const devices: Record<string, Device[]> = {
    lenovo: [
      { id: 'lenovo_ideapad_5', brand: 'Lenovo', model: 'IdeaPad 5' },
      { id: 'lenovo_thinkpad_x1', brand: 'Lenovo', model: 'ThinkPad X1' },
    ],
    dell: [
      { id: 'dell_xps_15', brand: 'Dell', model: 'XPS 15' },
      { id: 'dell_latitude_5420', brand: 'Dell', model: 'Latitude 5420' },
    ],
    hp: [
      { id: 'hp_pavilion', brand: 'HP', model: 'Pavilion' },
      { id: 'hp_elitebook', brand: 'HP', model: 'EliteBook' },
    ],
  };

  const handleDeviceSelect = (deviceId: string) => {
    router.push(`/diagnose?device=${deviceId}`);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="border-b border-neutral-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => router.push('/')}>
              ← Back
            </Button>
            <div className="text-center">
              <h1 className="text-xl font-semibold text-neutral-900">Select Your Device</h1>
              <p className="text-sm text-neutral-500">Choose your laptop model to continue</p>
            </div>
            <Button variant="outline" onClick={() => router.push('/guides')}>
              Browse Guides
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Brand Selection */}
        <div className="mb-12">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Select Brand</h2>
          <div className="grid grid-cols-3 gap-4">
            {brands.map((brand) => (
              <button
                key={brand.id}
                onClick={() => setSelectedBrand(brand.id)}
                className={`p-6 rounded-xl border-2 transition-all duration-200 ${
                  selectedBrand === brand.id
                    ? 'border-neutral-900 bg-neutral-50 shadow-medium'
                    : 'border-neutral-200 hover:border-neutral-300 hover:shadow-soft'
                }`}
              >
                <div className="text-2xl font-bold text-neutral-900 mb-1">{brand.name}</div>
                <div className="text-sm text-neutral-500">{brand.count} models</div>
              </button>
            ))}
          </div>
        </div>

        {/* Device Selection */}
        {selectedBrand && (
          <div className="animate-slide-up">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">Select Model</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {devices[selectedBrand].map((device) => (
                <Card
                  key={device.id}
                  hover
                  onClick={() => handleDeviceSelect(device.id)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between mb-2">
                      <Badge variant="default">{device.brand}</Badge>
                    </div>
                    <CardTitle>{device.model}</CardTitle>
                    <CardDescription>Click to start diagnosis</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="aspect-video bg-neutral-100 rounded-lg flex items-center justify-center text-neutral-400">
                      📱
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {!selectedBrand && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">💻</div>
            <p className="text-neutral-500">Select a brand above to view available models</p>
          </div>
        )}
      </main>
    </div>
  );
}
