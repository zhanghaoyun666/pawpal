export interface Pet {
  id: string;
  name: string;
  breed: string;
  age: string;
  ageValue: number; // roughly in months/years for sorting if needed
  distance: string;
  image: string;
  category: 'dog' | 'cat' | 'rabbit' | 'other';
  price?: string;
  gender?: 'Male' | 'Female';
  weight?: string;
  tags?: string[];
  owner?: {
    name: string;
    role: string;
    image: string;
  };
  health?: {
    vaccinated: boolean;
    neutered: boolean;
    microchipped: boolean;
    chipNumber?: string;
  };
  description?: string;
  location: string;
  isAdopted?: boolean; // 标记宠物是否已被领养
}

export interface Category {
  id: string;
  name: string;
  icon?: string;
  image?: string;
  isIcon: boolean;
}

// 消息发送状态
export type MessageStatus = 'sending' | 'sent' | 'failed';

export interface Message {
  id: string;
  sender: 'user' | 'coordinator';
  text: string;
  timestamp: string;
  isRead?: boolean;
  status?: MessageStatus;
  imageUrl?: string;
}

export interface ChatSession {
  id: string;
  petId: string;
  petName: string;
  petImage: string;
  coordinatorName: string;
  coordinatorImage: string;
  otherParticipantName: string;
  otherParticipantImage: string;
  otherParticipantRole: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
}