# Video Creator Mobile App - React Native

React Native cross-platform mobile app for iOS and Android.

## Project Structure

```
mobile/
├── src/
│   ├── screens/
│   │   ├── Auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   └── SignupScreen.tsx
│   │   ├── Dashboard/
│   │   │   └── DashboardScreen.tsx
│   │   ├── Videos/
│   │   │   ├── VideoListScreen.tsx
│   │   │   ├── VideoDetailScreen.tsx
│   │   │   └── VideoCreatorScreen.tsx
│   │   ├── Analytics/
│   │   │   └── AnalyticsScreen.tsx
│   │   └── Settings/
│   │       └── SettingsScreen.tsx
│   ├── components/
│   │   ├── VideoCard.tsx
│   │   ├── MetricCard.tsx
│   │   └── Button.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── upload.ts
│   ├── store/
│   │   ├── auth/
│   │   ├── videos/
│   │   └── analytics/
│   ├── navigation/
│   │   └── RootNavigator.tsx
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── helpers.ts
├── android/
├── ios/
├── app.json
├── package.json
└── tsconfig.json
```

## Technology Stack

```json
{
  "name": "video-creator-mobile",
  "version": "1.0.0",
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.73.2",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "axios": "^1.6.5",
    "@react-native-async-storage/async-storage": "^1.21.0",
    "react-native-video": "^5.2.1",
    "react-native-image-picker": "^7.0.3",
    "react-native-fs": "^2.20.0",
    "@react-native-firebase/messaging": "^18.7.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-native": "^0.72.8",
    "typescript": "^5.3.3"
  }
}
```

## Key Screens

### 1. Dashboard Screen
```typescript
// src/screens/Dashboard/DashboardScreen.tsx

import React, { useEffect, useState } from 'react';
import { View, ScrollView, RefreshControl, StyleSheet } from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import MetricCard from '../../components/MetricCard';
import VideoCard from '../../components/VideoCard';
import { fetchDashboardData } from '../../store/dashboard/actions';

const DashboardScreen: React.FC = () => {
  const dispatch = useDispatch();
  const { metrics, recentVideos, loading } = useSelector(state => state.dashboard);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    dispatch(fetchDashboardData());
  }, []);
  
  const onRefresh = async () => {
    setRefreshing(true);
    await dispatch(fetchDashboardData());
    setRefreshing(false);
  };
  
  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.metricsRow}>
        <MetricCard
          title="Total Views"
          value={metrics.totalViews}
          change={metrics.viewsChange}
          icon="eye"
        />
        <MetricCard
          title="Engagement"
          value={`${metrics.engagement}%`}
          change={metrics.engagementChange}
          icon="heart"
        />
      </View>
      
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Videos</Text>
        {recentVideos.map(video => (
          <VideoCard key={video.id} video={video} />
        ))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  metricsRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 12
  },
  section: {
    padding: 16
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12
  }
});

export default DashboardScreen;
```

### 2. Video Creator Screen
```typescript
// src/screens/Videos/VideoCreatorScreen.tsx

import React, { useState } from 'react';
import { View, TextInput, Button, Alert } from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import { uploadVideo } from '../../services/upload';

const VideoCreatorScreen: React.FC = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [videoFile, setVideoFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const selectVideo = async () => {
    const result = await launchImageLibrary({
      mediaType: 'video',
      quality: 1
    });
    
    if (result.assets && result.assets[0]) {
      setVideoFile(result.assets[0]);
    }
  };
  
  const handleUpload = async () => {
    if (!videoFile || !title) {
      Alert.alert('Error', 'Please select a video and enter a title');
      return;
    }
    
    setUploading(true);
    
    try {
      await uploadVideo(
        videoFile,
        { title, description },
        (progress) => setProgress(progress)
      );
      
      Alert.alert('Success', 'Video uploaded successfully!');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setUploading(false);
    }
  };
  
  return (
    <View style={styles.container}>
      <TextInput
        placeholder="Video Title"
        value={title}
        onChangeText={setTitle}
        style={styles.input}
      />
      
      <TextInput
        placeholder="Description"
        value={description}
        onChangeText={setDescription}
        multiline
        style={styles.textArea}
      />
      
      <Button title="Select Video" onPress={selectVideo} />
      
      {videoFile && (
        <Text>Selected: {videoFile.fileName}</Text>
      )}
      
      {uploading && (
        <ProgressBar progress={progress} />
      )}
      
      <Button
        title="Upload Video"
        onPress={handleUpload}
        disabled={uploading}
      />
    </View>
  );
};
```

### 3. API Service
```typescript
// src/services/api.ts

import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class APIClient {
  private client: AxiosInstance;
  private token: string | null = null;
  
  constructor() {
    this.client = axios.create({
      baseURL: 'https://api.ytvideocreator.com',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Request interceptor - add auth token
    this.client.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    
    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired - redirect to login
          this.handleUnauthorized();
        }
        return Promise.reject(error);
      }
    );
  }
  
  // Authentication
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', {
      email,
      password
    });
    
    const { token, user } = response.data;
    
    await AsyncStorage.setItem('auth_token', token);
    this.token = token;
    
    return user;
  }
  
  async logout() {
    await AsyncStorage.removeItem('auth_token');
    this.token = null;
  }
  
  // Videos
  async getVideos(page: number = 1) {
    const response = await this.client.get('/videos', {
      params: { page, limit: 20 }
    });
    return response.data;
  }
  
  async getVideo(id: string) {
    const response = await this.client.get(`/videos/${id}`);
    return response.data;
  }
  
  async deleteVideo(id: string) {
    await this.client.delete(`/videos/${id}`);
  }
  
  // Analytics
  async getAnalytics(period: string = 'week') {
    const response = await this.client.get('/analytics', {
      params: { period }
    });
    return response.data;
  }
  
  private handleUnauthorized() {
    // Navigate to login screen
    // This would be handled by navigation context
  }
}

export default new APIClient();
```

### 4. Upload Service
```typescript
// src/services/upload.ts

import RNFS from 'react-native-fs';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface VideoMetadata {
  title: string;
  description?: string;
}

export async function uploadVideo(
  file: any,
  metadata: VideoMetadata,
  onProgress: (progress: number) => void
): Promise<any> {
  const token = await AsyncStorage.getItem('auth_token');
  
  const uploadUrl = 'https://api.ytvideocreator.com/videos/upload';
  
  const uploadResult = await RNFS.uploadFiles({
    toUrl: uploadUrl,
    files: [
      {
        name: 'video',
        filename: file.fileName,
        filepath: file.uri,
        filetype: file.type
      }
    ],
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    fields: {
      title: metadata.title,
      description: metadata.description || ''
    },
    begin: () => {
      console.log('Upload started');
    },
    progress: (data) => {
      const progress = data.totalBytesSent / data.totalBytesExpectedToSend;
      onProgress(progress);
    }
  }).promise;
  
  if (uploadResult.statusCode === 200) {
    return JSON.parse(uploadResult.body);
  } else {
    throw new Error('Upload failed');
  }
}
```

## Native Features

### Push Notifications
```typescript
// Configure Firebase Cloud Messaging

import messaging from '@react-native-firebase/messaging';

async function requestUserPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Authorization status:', authStatus);
    getFCMToken();
  }
}

async function getFCMToken() {
  const token = await messaging().getToken();
  console.log('FCM Token:', token);
  // Send token to backend
  await api.updateFCMToken(token);
}

// Handle foreground messages
messaging().onMessage(async remoteMessage => {
  Alert.alert('New Notification', remoteMessage.notification.body);
});
```

### Camera Integration
```typescript
import { launchCamera } from 'react-native-image-picker';

const captureVideo = async () => {
  const result = await launchCamera({
    mediaType: 'video',
    videoQuality: 'high',
    durationLimit: 60  // 60 seconds max
  });
  
  if (result.assets && result.assets[0]) {
    return result.assets[0];
  }
};
```

## Build & Deployment

### iOS (TestFlight)
```bash
# Build for iOS
cd ios
pod install
cd ..
npx react-native run-ios --configuration Release

# Archive and upload to TestFlight
xcodebuild archive -workspace ios/VideoCreator.xcworkspace \
  -scheme VideoCreator \
  -archivePath build/VideoCreator.xcarchive

xcrun altool --upload-app --file build/VideoCreator.ipa \
  --username "your@email.com" \
  --password "app-specific-password"
```

### Android (Google Play Beta)
```bash
# Build for Android
cd android
./gradlew assembleRelease

# Build AAB for Play Store
./gradlew bundleRelease

# Upload to Google Play Console
# Manual upload via console.play.google.com
```

---

**Mobile app ready for beta release!** 📱
