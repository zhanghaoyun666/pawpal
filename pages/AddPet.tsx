import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const CHINA_REGIONS: Record<string, string[]> = {
    '北京市': ['东城区', '西城区', '朝阳区', '丰台区', '石景山区', '海淀区', '门头沟区', '房山区', '通州区', '顺义区', '昌平区', '大兴区', '怀柔区', '平谷区', '密云区', '延庆区'],
    '上海市': ['黄浦区', '徐汇区', '长宁区', '静安区', '普陀区', '虹口区', '杨浦区', '闵行区', '宝山区', '嘉定区', '浦东新区', '金山区', '松江区', '青浦区', '奉贤区', '崇明区'],
    '广东省': ['广州市', '深圳市', '珠海市', '汕头市', '佛山市', '江门市', '湛江市', '茂名市', '肇庆市', '惠州市', '梅州市', '汕尾市', '河源市', '阳江市', '清远市', '东莞市', '中山市', '潮州市', '揭阳市', '云浮市'],
    '浙江省': ['杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市'],
    '江苏省': ['南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市'],
    '湖北省': ['武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '鄂州市', '荆门市', '孝感市', '荆州市', '黄冈市', '咸宁市', '随州市', '恩施州'],
    '四川省': ['成都市', '自贡市', '攀枝花市', '泸州市', '德阳市', '绵阳市', '广元市', '遂宁市', '内江市', '乐山市', '南充市', '眉山市', '宜宾市', '广安市', '达州市', '雅安市', '巴中市', '资阳市', '阿坝州', '甘孜州', '凉山州'],
    '重庆市': ['渝中区', '大渡口区', '江北区', '沙坪坝区', '九龙坡区', '南岸区', '北碚区', '綦江区', '大足区', '渝北区', '巴南区', '黔江区', '长寿区', '江津区', '合川区', '永川区', '南川区', '璧山区', '铜梁区', '潼南区', '荣昌区', '开州区', '梁平区', '武隆区'],
    '福建省': ['福州市', '厦门市', '莆田市', '三明市', '泉州市', '漳州市', '南平市', '龙岩市', '宁德市'],
    '山东省': ['济南市', '青岛市', '淄博市', '枣庄市', '东营市', '烟台市', '潍坊市', '济宁市', '泰安市', '威海市', '日照市', '临沂市', '德州市', '聊城市', '滨州市', '菏泽市'],
    '湖南省': ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界市', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西州'],
    '陕西省': ['西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市'],
    '天津市': ['和平区', '河东区', '河西区', '南开区', '河北区', '红桥区', '滨海新区', '东丽区', '西青区', '津南区', '北辰区', '武清区', '宝坻区', '宁河区', '静海区', '蓟州区'],
    '河北省': ['石家庄市', '唐山市', '秦皇岛市', '邯郸市', '邢台市', '保定市', '张家口市', '承德市', '沧州市', '廊坊市', '衡水市'],
    '河南省': ['郑州市', '开封市', '洛阳市', '平顶山市', '安阳市', '鹤壁市', '新乡市', '焦作市', '濮阳市', '许昌市', '漯河市', '三门峡市', '南阳市', '商丘市', '信阳市', '周口市', '驻马店市'],
    '辽宁省': ['沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市', '丹东市', '锦州市', '营口市', '阜新市', '辽阳市', '盘锦市', '铁岭市', '朝阳市', '葫芦岛市'],
    '安徽省': ['合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市', '淮北市', '铜陵市', '安庆市', '黄山市', '滁州市', '阜阳市', '宿州市', '六安市', '亳州市', '池州市', '宣城市'],
    '江西省': ['南昌市', '景德镇市', '萍乡市', '九江市', '新余市', '鹰潭市', '赣州市', '吉安市', '宜春市', '抚州市', '上饶市'],
    '广西壮族自治区': ['南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港市', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市'],
    '海南省': ['海口市', '三亚市', '三沙市', '儋州市'],
    '贵州省': ['贵阳市', '六盘水市', '遵义市', '安顺市', '毕节市', '铜仁市', '黔西南州', '黔东南州', '黔南州'],
    '云南省': ['昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市', '楚雄州', '红河州', '文山州', '西双版纳州', '大理州', '德宏州', '怒江州', '迪庆州'],
    '吉林省': ['长春市', '吉林市', '四平市', '辽源市', '通化市', '白山市', '松原市', '白城市', '延边州'],
    '黑龙江省': ['哈尔滨市', '齐齐哈尔市', '鸡西市', '鹤岗市', '双鸭山市', '大庆市', '伊春市', '佳木斯市', '七台河市', '牡丹江市', '黑河市', '绥化市', '大兴安岭地区'],
    '山西省': ['太原市', '大同市', '阳泉市', '长治市', '晋城市', '朔州市', '晋中市', '运城市', '忻州市', '临汾市', '吕梁市'],
    '内蒙古自治区': ['呼和浩特市', '包头市', '乌海市', '赤峰市', '通辽市', '鄂尔多斯市', '呼伦贝尔市', '巴彦淖尔市', '乌兰察布市', '兴安盟', '锡林郭勒盟', '阿拉善盟'],
    '甘肃省': ['兰州市', '嘉峪关市', '金昌市', '白银市', '天水市', '武威市', '张掖市', '平凉市', '酒泉市', '庆阳市', '定西市', '陇南市', '临夏州', '甘南州'],
    '青海省': ['西宁市', '海东市', '海北州', '黄南州', '海南州', '果洛州', '玉树州', '海西州'],
    '宁夏回族自治区': ['银川市', '石嘴山市', '吴忠市', '固原市', '中卫市'],
    '新疆维吾尔自治区': ['乌鲁木齐市', '克拉玛依市', '吐鲁番市', '哈密市', '昌吉州', '博尔塔拉州', '巴音郭楞州', '阿克苏地区', '克孜勒苏州', '喀什地区', '和田地区', '伊犁州', '塔城地区', '阿勒泰地区']
};

const AddPet: React.FC = () => {
    const navigate = useNavigate();
    const { user, refreshData } = useApp();
    const [formData, setFormData] = useState({
        name: '',
        breed: '',
        age_text: '',
        age_value: 0,
        image_url: '',
        category: 'dog',
        price: '',
        gender: 'Male',
        description: '',
        weight: '',
        vaccinated: false,
        neutered: false,
        microchipped: false
    });

    const [location, setLocation] = useState({
        province: '',
        city: ''
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target as HTMLInputElement;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : (name === 'age_value' ? parseInt(value) || 0 : value)
        }));
    };

    const handleLocationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const { name, value } = e.target;
        setLocation(prev => ({
            ...prev,
            [name]: value,
            ...(name === 'province' ? { city: '' } : {})
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) {
            alert('请先登录');
            return;
        }

        if (!location.province || !location.city) {
            alert('请选择完整的位置信息');
            return;
        }

        try {
            const petData = {
                ...formData,
                location: `${location.province} ${location.city}`,
                health_info: {
                    vaccinated: formData.vaccinated,
                    neutered: formData.neutered,
                    microchipped: formData.microchipped
                },
                owner_id: user.id,
                tags: []
            };
            console.log('Submitting pet data:', petData);
            await api.createPet(petData);
            await refreshData(); // Call refreshData after successful pet creation
            alert('发布成功！');
            navigate('/');
        } catch (error: any) {
            console.error(error);
            alert('发布失败：' + (error.response?.data?.detail || error.message || '请检查表单是否填写完整'));
        }
    };

    return (
        <div className="min-h-screen bg-background-light dark:bg-background-dark p-4 max-w-md mx-auto pb-24">
            <header className="flex items-center mb-6">
                <button onClick={() => navigate(-1)} className="text-text-main dark:text-text-main-dark mr-4">
                    <span className="material-symbols-outlined text-2xl">arrow_back</span>
                </button>
                <h1 className="text-xl font-bold text-text-main dark:text-text-main-dark">发布送养信息</h1>
            </header>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">宠物昵称</label>
                    <input name="name" placeholder="例如：乐乐" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" required />
                </div>

                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">宠物品种</label>
                    <input name="breed" placeholder="例如：比熊 / 贵宾" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" required />
                </div>

                <div className="flex gap-4">
                    <div className="flex-1 space-y-1">
                        <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">展示年龄</label>
                        <input name="age_text" placeholder="2岁 / 3个月" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" required />
                    </div>
                    <div className="w-28 space-y-1">
                        <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">月龄(排序用)</label>
                        <input name="age_value" type="number" placeholder="24" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" required />
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">所在城市</label>
                    <div className="flex gap-2">
                        <select
                            name="province"
                            value={location.province}
                            onChange={handleLocationChange}
                            className="flex-1 p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none"
                            required
                        >
                            <option value="">选择省份</option>
                            {Object.keys(CHINA_REGIONS).map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                        <select
                            name="city"
                            value={location.city}
                            onChange={handleLocationChange}
                            className="flex-1 p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none"
                            required
                            disabled={!location.province}
                        >
                            <option value="">选择城市</option>
                            {location.province && CHINA_REGIONS[location.province].map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">领养费用 (不填则显示免费)</label>
                    <input name="price" placeholder="例如：1000 / 免费" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" />
                </div>

                <div className="flex gap-4">
                    <div className="flex-1 space-y-1">
                        <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">类别</label>
                        <select name="category" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none">
                            <option value="dog">狗狗</option>
                            <option value="cat">猫猫</option>
                            <option value="rabbit">兔子</option>
                            <option value="other">其他</option>
                        </select>
                    </div>
                    <div className="flex-1 space-y-1">
                        <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">性别</label>
                        <select name="gender" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none">
                            <option value="Male">公</option>
                            <option value="Female">母</option>
                        </select>
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">宠物体重 (例如：5kg)</label>
                    <input name="weight" placeholder="例如：5kg / 10斤" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" />
                </div>

                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">图片链接</label>
                    <input name="image_url" placeholder="支持 URL 或 Base64" onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none" required />
                </div>

                {formData.image_url && (
                    <div className="w-full h-48 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                        <img
                            src={formData.image_url}
                            alt="预览"
                            className="w-full h-full object-cover"
                            onError={(e) => {
                                (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x300?text=Invalid+Image+URL';
                            }}
                        />
                    </div>
                )}

                <div className="space-y-3 p-4 bg-gray-50 dark:bg-white/5 rounded-2xl border border-gray-100 dark:border-white/10">
                    <h3 className="text-base font-bold text-text-main dark:text-text-main-dark mb-1">健康状况</h3>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-primary">vaccines</span>
                            <span className="text-sm font-medium">是否接种疫苗</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" name="vaccinated" checked={formData.vaccinated} onChange={handleChange} className="sr-only peer" />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-primary">medical_services</span>
                            <span className="text-sm font-medium">是否绝育</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" name="neutered" checked={formData.neutered} onChange={handleChange} className="sr-only peer" />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-primary">potted_plant</span>
                            <span className="text-sm font-medium">是否植入芯片</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" name="microchipped" checked={formData.microchipped} onChange={handleChange} className="sr-only peer" />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-sm font-medium text-text-muted dark:text-text-muted ml-1">详细描述</label>
                    <textarea name="description" placeholder="关于宠物的性格、健康状况等..." rows={4} onChange={handleChange} className="w-full p-3 rounded-lg border dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark focus:border-primary focus:outline-none"></textarea>
                </div>

                <button type="submit" className="bg-primary text-[#0f2906] p-4 rounded-xl font-bold mt-4 active:scale-95 transition-transform shadow-lg shadow-primary/20">确认发布</button>
            </form>
        </div>
    );
};

export default AddPet;
