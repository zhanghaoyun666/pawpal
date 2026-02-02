import { Pet, ChatSession, Category } from './types';

export const PETS: Pet[] = [
  {
    id: '1',
    name: 'Max',
    breed: '金毛寻回犬',
    age: '2岁',
    ageValue: 24,
    distance: '2.5 km',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBmt5x-CxMOJ03itG670Vucina7plV3B8kCeTIQ-gvlnNS8TvUBWsdzzPSqAkfWUGlG9egCvGwrFr-SS6mAWWl4_u07U-FtnMqhZC8jcMRMeWbNsG2OFU8lVSPp3BJXUgeZrc8aSyTiwzbuI3VfmlDwIhZmHmzTfllJwLdEe93yYH3ZoKsP2vr_VhQnBlR7qF-X0JHHCtJLcfJc9gdHSQ8I9ae3YO4Db78bUnGuKKzzsKxiIxPMEw4mQ33eJZ-2G13Ua67Ccq_F5_8',
    category: 'dog',
    price: '$250',
    gender: 'Male',
    weight: '28 公斤',
    tags: ['金毛寻回犬', '纯种', '已定点如厕'],
    owner: {
      name: 'Sarah Wilson',
      role: '送养人',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDPVpLiTvjm3XOaQwsBrF6Qrltmi8yr7_fSnxcOTBNe2iwxvEZ5IuLrtEkD4T9Yp1mDiX9wrRVzH2a6zzTeUKoAaP90CdNTbpDLpEQkqFQEBBF6iUbvMGFj93CvOllMZo9jdmXquulhZY1umcQKVWu4jIoBn3UPTzlGRCZ_XdXxzRAFA5XtDAy0MhFV4I_rIX2m8SoMWjPToqk63I5x780gfOc3R7hWC3Nf0iOC70HGXlInN7XjLA0fgq5W7LX8ERxXPJ2YAkeIIjw'
    },
    health: {
      vaccinated: true,
      neutered: true,
      microchipped: true,
      chipNumber: '9821...'
    },
    description: 'Max 是一只无比可爱的金毛寻回犬，他对见到的每个人都非常热情。他性格沉稳，但非常喜欢每天的散步和在公园里玩丢球游戏。他与其他狗狗相处融洽，对小孩子也很温柔。他正在寻找一个充满爱的永远的家，希望能参与到家庭活动中去。',
    location: '上海, 浦东新区',
    isAdopted: true // 已领养示例
  },
  {
    id: '2',
    name: 'Luna',
    breed: '波斯猫',
    age: '1岁',
    ageValue: 12,
    distance: '3.8 km',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCi1fcAkRLyoTYmYwCj-ST7owJzSKb9v_4dg2JQQhh5xSP1raVAr-K7ZK-79E5bmfpWvEioNXYyViZMPHEMa35j1txD5WU3ioAVqP6LSosXl1EFOkzTEBlUvNOugT-VR8kkVmulXSlbL9Vyu2wXx91W-_OrjpXKVGOXw9ErjV97BJk_I54O9ynx2bxUpD5LQgGrINxqVsjtafJV4RDd9P8dgnfE0S_IF2CnWcUPtn1tlU2VoxrW_WhUNsGsJ3GkYOhXoGwz2EDZKg8',
    category: 'cat',
    location: '上海, 静安区',
    owner: {
      name: 'Emily Chen',
      role: '救助站志愿者',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBBPhotk3xjpng2lG1eVnPl8LCPT16pAinrsh1zTSZKto270J6vCRdhCN2nPcvPqzz6jTKEL_T5N_PCrsQ58oIEIS7h7B9xe9mURXw06C1LRvbofa-MOJOHfn_GNkDIj1j5-WfIHwlSF_8_CkanEGMj_RXs8oIpArrJSyEAcxdLV3Q4qDuA1uMRbLCZByPpDg4l4ft9ZRPsYXmdZ5IXtGbXB1PAbmt_jGfHLibk9IFemYOdWbTGhJ6eS9CDAfY0isE-O0Y-3MSkwk4'
    },
    description: 'Luna 是一只优雅安静的波斯猫。她喜欢在阳光下打盹。需要定期的梳理毛发。',
    price: '$150',
    gender: 'Female',
    weight: '4 公斤'
  },
  {
    id: '3',
    name: 'Charlie',
    breed: '比格犬',
    age: '4个月',
    ageValue: 4,
    distance: '1.2 km',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBw079FcE7B4avvHfTUog1hzVrUOgCmceMw9b6-ahlQJTD4E59XczTHPlHySUCv5TIcuL0P57rHfspwY4BlFKII56Yl-Fnd5RcHP7iaY0BwzRizTlRf_p8n9JAUZCE4xY3xzJXebeTQrHYmY5edvHkyWILgVmxsuJimR9LqYb23VEeq1iihvvT-JJkFVZzaJNSUDtBjr2Ggc7uOH-i3iy8iVdA_WfrGyxotZKnM_yK9iWZ0TUiU5BPUj7b3WFhiJdqRdYbA3qM8JUg',
    category: 'dog',
    location: '上海, 黄浦区',
    owner: {
      name: 'Mike Ross',
      role: '送养人',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBBPhotk3xjpng2lG1eVnPl8LCPT16pAinrsh1zTSZKto270J6vCRdhCN2nPcvPqzz6jTKEL_T5N_PCrsQ58oIEIS7h7B9xe9mURXw06C1LRvbofa-MOJOHfn_GNkDIj1j5-WfIHwlSF_8_CkanEGMj_RXs8oIpArrJSyEAcxdLV3Q4qDuA1uMRbLCZByPpDg4l4ft9ZRPsYXmdZ5IXtGbXB1PAbmt_jGfHLibk9IFemYOdWbTGhJ6eS9CDAfY0isE-O0Y-3MSkwk4'
    },
    description: 'Charlie 是一只精力充沛的小狗，还在学习上厕所。非常适合活跃的家庭。',
    price: '$300',
    gender: 'Male',
    weight: '6 公斤'
  },
  {
    id: '4',
    name: 'Bella',
    breed: '拉布拉多',
    age: '3岁',
    ageValue: 36,
    distance: '5.0 km',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC7SudbnfpF51rEVIRuLlKyhoBR_PK4J4oIwGucfPdXzZqu3YJqZT7VWkcFROtAaO5t1AqQ8iSKTA8IqvFJfMcJOkEt7egvKE2MYqdb7OpY13sStqXw7tkjFn3bIlkUEoKTn2NqptCN1jHO5cj4WW_ylkzl1rUz4zt_zhb_-tQJq5KKsmquaMNYqim9L9a5iYrYW1pqdUDVPGvRiZ275tL1YeZO9alRzxOhyhlEg9JLcNoEcx8hT1aylM_dzIG6Bxh-WDcnx5qzPWA',
    category: 'dog',
    location: '上海, 闵行区',
    owner: {
      name: 'Jenny Kim',
      role: '救助中心',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDPVpLiTvjm3XOaQwsBrF6Qrltmi8yr7_fSnxcOTBNe2iwxvEZ5IuLrtEkD4T9Yp1mDiX9wrRVzH2a6zzTeUKoAaP90CdNTbpDLpEQkqFQEBBF6iUbvMGFj93CvOllMZo9jdmXquulhZY1umcQKVWu4jIoBn3UPTzlGRCZ_XdXxzRAFA5XtDAy0MhFV4I_rIX2m8SoMWjPToqk63I5x780gfOc3R7hWC3Nf0iOC70HGXlInN7XjLA0fgq5W7LX8ERxXPJ2YAkeIIjw'
    },
    description: 'Bella 非常温顺，是完美的家庭伴侣犬。',
    price: '$200',
    gender: 'Female',
    weight: '25 公斤'
  }
];

export const CATEGORIES: Category[] = [
  { id: 'all', name: '全部', icon: 'pets', isIcon: true },
  { 
    id: 'dog', 
    name: '狗狗', 
    image: 'https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Dog%20Face.png', 
    isIcon: false 
  },
  { 
    id: 'cat', 
    name: '猫猫', 
    image: 'https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Cat%20Face.png', 
    isIcon: false 
  },
  { 
    id: 'rabbit', 
    name: '兔子', 
    image: 'https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Rabbit%20Face.png', 
    isIcon: false 
  },
  { id: 'other', name: '其他', icon: 'more_horiz', isIcon: true }
];

export const CHATS: ChatSession[] = [
  {
    id: '1',
    petId: '1',
    petName: 'Max',
    petImage: PETS[0].image,
    coordinatorName: 'Sarah Wilson',
    coordinatorImage: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDPVpLiTvjm3XOaQwsBrF6Qrltmi8yr7_fSnxcOTBNe2iwxvEZ5IuLrtEkD4T9Yp1mDiX9wrRVzH2a6zzTeUKoAaP90CdNTbpDLpEQkqFQEBBF6iUbvMGFj93CvOllMZo9jdmXquulhZY1umcQKVWu4jIoBn3UPTzlGRCZ_XdXxzRAFA5XtDAy0MhFV4I_rIX2m8SoMWjPToqk63I5x780gfOc3R7hWC3Nf0iOC70HGXlInN7XjLA0fgq5W7LX8ERxXPJ2YAkeIIjw',
    lastMessage: '好的，我们约周六见面！',
    lastMessageTime: '09:45 AM',
    unreadCount: 0
  },
  {
    id: '2',
    petId: '2',
    petName: 'Luna',
    petImage: PETS[1].image,
    coordinatorName: 'Emily Chen',
    coordinatorImage: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBBPhotk3xjpng2lG1eVnPl8LCPT16pAinrsh1zTSZKto270J6vCRdhCN2nPcvPqzz6jTKEL_T5N_PCrsQ58oIEIS7h7B9xe9mURXw06C1LRvbofa-MOJOHfn_GNkDIj1j5-WfIHwlSF_8_CkanEGMj_RXs8oIpArrJSyEAcxdLV3Q4qDuA1uMRbLCZByPpDg4l4ft9ZRPsYXmdZ5IXtGbXB1PAbmt_jGfHLibk9IFemYOdWbTGhJ6eS9CDAfY0isE-O0Y-3MSkwk4',
    lastMessage: '她已经打完疫苗了。',
    lastMessageTime: '昨天',
    unreadCount: 2
  }
];