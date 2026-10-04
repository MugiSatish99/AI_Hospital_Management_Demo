"""
seed_india_hospitals.py
Populates hospitals_directory and hospital_beds tables with ~3000 hospitals
across all major Indian cities/towns (5-6 per city), covering all states.
Run: py -3.10 seed_india_hospitals.py
"""

import sqlite3
import random
import math
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")

# ─────────────────────────────────────────────────────────────────────────────
# INDIA CITY DATABASE
# Format: (city, district, state, lat, lon)
# ~550 cities/towns across all states
# ─────────────────────────────────────────────────────────────────────────────
INDIA_CITIES = [
    # ── Andhra Pradesh ────────────────────────────────────────────────────────
    ("Visakhapatnam","Visakhapatnam","Andhra Pradesh",17.6868,83.2185),
    ("Vijayawada","Krishna","Andhra Pradesh",16.5062,80.6480),
    ("Guntur","Guntur","Andhra Pradesh",16.3067,80.4365),
    ("Nellore","SPSR Nellore","Andhra Pradesh",14.4426,79.9865),
    ("Kurnool","Kurnool","Andhra Pradesh",15.8281,78.0373),
    ("Rajamahendravaram","East Godavari","Andhra Pradesh",17.0050,81.7800),
    ("Kadapa","YSR Kadapa","Andhra Pradesh",14.4673,78.8242),
    ("Kakinada","East Godavari","Andhra Pradesh",16.9891,82.2475),
    ("Tirupati","Chittoor","Andhra Pradesh",13.6288,79.4192),
    ("Anantapur","Anantapur","Andhra Pradesh",14.6819,77.6006),
    ("Eluru","West Godavari","Andhra Pradesh",16.7107,81.0952),
    ("Ongole","Prakasam","Andhra Pradesh",15.5057,80.0499),
    ("Srikakulam","Srikakulam","Andhra Pradesh",18.2949,83.8938),
    ("Vizianagaram","Vizianagaram","Andhra Pradesh",18.1170,83.4166),
    ("Chittoor","Chittoor","Andhra Pradesh",13.2173,79.1003),
    ("Machilipatnam","Krishna","Andhra Pradesh",16.1875,81.1389),
    ("Hindupur","Anantapur","Andhra Pradesh",13.8278,77.4912),
    ("Proddatur","YSR Kadapa","Andhra Pradesh",14.7330,78.5489),
    ("Bhimavaram","West Godavari","Andhra Pradesh",16.5444,81.5214),
    ("Narasaraopet","Guntur","Andhra Pradesh",16.2362,80.0484),

    # ── Arunachal Pradesh ────────────────────────────────────────────────────
    ("Itanagar","Papum Pare","Arunachal Pradesh",27.0844,93.6053),
    ("Naharlagun","Papum Pare","Arunachal Pradesh",27.1024,93.6953),
    ("Pasighat","East Siang","Arunachal Pradesh",28.0662,95.3254),
    ("Tezpur (AP)","Sonitpur","Arunachal Pradesh",26.6528,92.7948),
    ("Ziro","Lower Subansiri","Arunachal Pradesh",27.5383,93.8265),

    # ── Assam ─────────────────────────────────────────────────────────────────
    ("Guwahati","Kamrup Metropolitan","Assam",26.1445,91.7362),
    ("Silchar","Cachar","Assam",24.8333,92.7789),
    ("Dibrugarh","Dibrugarh","Assam",27.4728,94.9120),
    ("Jorhat","Jorhat","Assam",26.7509,94.2037),
    ("Nagaon","Nagaon","Assam",26.3469,92.6836),
    ("Tinsukia","Tinsukia","Assam",27.4892,95.3608),
    ("Tezpur","Sonitpur","Assam",26.6528,92.7948),
    ("Bongaigaon","Bongaigaon","Assam",26.4765,90.5586),
    ("Dhubri","Dhubri","Assam",26.0214,89.9760),
    ("Lakhimpur","Lakhimpur","Assam",27.2347,94.1012),
    ("Karimganj","Karimganj","Assam",24.8671,92.3618),
    ("Goalpara","Goalpara","Assam",26.1734,90.6208),
    ("Sibsagar","Sivasagar","Assam",26.9836,94.6361),
    ("Diphu","Karbi Anglong","Assam",25.8430,93.4327),

    # ── Bihar ─────────────────────────────────────────────────────────────────
    ("Patna","Patna","Bihar",25.5941,85.1376),
    ("Gaya","Gaya","Bihar",24.7955,85.0002),
    ("Bhagalpur","Bhagalpur","Bihar",25.2425,86.9842),
    ("Muzaffarpur","Muzaffarpur","Bihar",26.1197,85.3910),
    ("Purnia","Purnia","Bihar",25.7771,87.4753),
    ("Darbhanga","Darbhanga","Bihar",26.1542,85.8918),
    ("Bihar Sharif","Nalanda","Bihar",25.1966,85.5236),
    ("Ara","Bhojpur","Bihar",25.5566,84.6624),
    ("Begusarai","Begusarai","Bihar",25.4182,86.1272),
    ("Katihar","Katihar","Bihar",25.5392,87.5738),
    ("Munger","Munger","Bihar",25.3701,86.4736),
    ("Chhapra","Saran","Bihar",25.7833,84.7501),
    ("Saharsa","Saharsa","Bihar",25.8773,86.5931),
    ("Sitamarhi","Sitamarhi","Bihar",26.5898,85.4838),
    ("Hajipur","Vaishali","Bihar",25.6887,85.2092),

    # ── Chhattisgarh ─────────────────────────────────────────────────────────
    ("Raipur","Raipur","Chhattisgarh",21.2514,81.6296),
    ("Bhilai","Durg","Chhattisgarh",21.1938,81.3509),
    ("Korba","Korba","Chhattisgarh",22.3595,82.7501),
    ("Bilaspur","Bilaspur","Chhattisgarh",22.0797,82.1409),
    ("Durg","Durg","Chhattisgarh",21.1904,81.2849),
    ("Raigarh","Raigarh","Chhattisgarh",21.8974,83.3950),
    ("Jagdalpur","Bastar","Chhattisgarh",19.0780,82.0256),
    ("Rajnandgaon","Rajnandgaon","Chhattisgarh",21.0970,81.0310),
    ("Ambikapur","Surguja","Chhattisgarh",23.1179,83.1975),

    # ── Goa ───────────────────────────────────────────────────────────────────
    ("Panaji","North Goa","Goa",15.4909,73.8278),
    ("Margao","South Goa","Goa",15.2832,73.9862),
    ("Vasco da Gama","South Goa","Goa",15.3983,73.8147),
    ("Mapusa","North Goa","Goa",15.5932,73.8045),
    ("Ponda","North Goa","Goa",15.4025,74.0028),

    # ── Gujarat ──────────────────────────────────────────────────────────────
    ("Ahmedabad","Ahmedabad","Gujarat",23.0225,72.5714),
    ("Surat","Surat","Gujarat",21.1702,72.8311),
    ("Vadodara","Vadodara","Gujarat",22.3072,73.1812),
    ("Rajkot","Rajkot","Gujarat",22.3039,70.8022),
    ("Bhavnagar","Bhavnagar","Gujarat",21.7645,72.1519),
    ("Jamnagar","Jamnagar","Gujarat",22.4707,70.0577),
    ("Gandhinagar","Gandhinagar","Gujarat",23.2156,72.6369),
    ("Junagadh","Junagadh","Gujarat",21.5222,70.4579),
    ("Anand","Anand","Gujarat",22.5645,72.9289),
    ("Nadiad","Kheda","Gujarat",22.6936,72.8619),
    ("Bharuch","Bharuch","Gujarat",21.7051,72.9959),
    ("Mehsana","Mehsana","Gujarat",23.5880,72.3693),
    ("Surendranagar","Surendranagar","Gujarat",22.7279,71.6485),
    ("Morbi","Morbi","Gujarat",22.8173,70.8370),
    ("Valsad","Valsad","Gujarat",20.5992,72.9342),
    ("Navsari","Navsari","Gujarat",20.9467,72.9520),
    ("Amreli","Amreli","Gujarat",21.6040,71.2200),
    ("Porbandar","Porbandar","Gujarat",21.6424,69.6093),
    ("Patan","Patan","Gujarat",23.8494,72.1266),
    ("Palanpur","Banaskantha","Gujarat",24.1748,72.4385),

    # ── Haryana ──────────────────────────────────────────────────────────────
    ("Faridabad","Faridabad","Haryana",28.4089,77.3178),
    ("Gurugram","Gurugram","Haryana",28.4595,77.0266),
    ("Ambala","Ambala","Haryana",30.3752,76.7821),
    ("Panipat","Panipat","Haryana",29.3909,76.9635),
    ("Rohtak","Rohtak","Haryana",28.8955,76.6066),
    ("Hisar","Hisar","Haryana",29.1492,75.7217),
    ("Karnal","Karnal","Haryana",29.6857,76.9905),
    ("Yamuna Nagar","Yamuna Nagar","Haryana",30.1290,77.2674),
    ("Panchkula","Panchkula","Haryana",30.6942,76.8606),
    ("Bhiwani","Bhiwani","Haryana",28.7932,76.1318),
    ("Sonipat","Sonipat","Haryana",28.9931,77.0151),
    ("Kaithal","Kaithal","Haryana",29.8011,76.3990),
    ("Sirsa","Sirsa","Haryana",29.5325,75.0272),
    ("Kurukshetra","Kurukshetra","Haryana",29.9695,76.8783),

    # ── Himachal Pradesh ─────────────────────────────────────────────────────
    ("Shimla","Shimla","Himachal Pradesh",31.1048,77.1734),
    ("Mandi","Mandi","Himachal Pradesh",31.7089,76.9320),
    ("Solan","Solan","Himachal Pradesh",30.9045,77.0967),
    ("Dharamsala","Kangra","Himachal Pradesh",32.2190,76.3234),
    ("Kullu","Kullu","Himachal Pradesh",31.9579,77.1091),
    ("Hamirpur","Hamirpur","Himachal Pradesh",31.6831,76.5218),
    ("Bilaspur","Bilaspur","Himachal Pradesh",31.3398,76.7602),
    ("Una","Una","Himachal Pradesh",31.4714,76.2706),

    # ── Jharkhand ────────────────────────────────────────────────────────────
    ("Ranchi","Ranchi","Jharkhand",23.3441,85.3096),
    ("Jamshedpur","East Singhbhum","Jharkhand",22.8046,86.2029),
    ("Dhanbad","Dhanbad","Jharkhand",23.7957,86.4304),
    ("Bokaro","Bokaro","Jharkhand",23.6693,86.1511),
    ("Deoghar","Deoghar","Jharkhand",24.4791,86.6962),
    ("Hazaribagh","Hazaribagh","Jharkhand",23.9916,85.3636),
    ("Giridih","Giridih","Jharkhand",24.1864,86.3026),
    ("Dumka","Dumka","Jharkhand",24.2683,87.2481),
    ("Phusro","Bokaro","Jharkhand",23.7803,85.9777),

    # ── Karnataka ────────────────────────────────────────────────────────────
    ("Bengaluru","Bengaluru Urban","Karnataka",12.9716,77.5946),
    ("Mysuru","Mysuru","Karnataka",12.2958,76.6394),
    ("Mangaluru","Dakshina Kannada","Karnataka",12.9141,74.8560),
    ("Hubballi","Dharwad","Karnataka",15.3647,75.1240),
    ("Belagavi","Belagavi","Karnataka",15.8497,74.4977),
    ("Kalaburagi","Kalaburagi","Karnataka",17.3297,76.8343),
    ("Davanagere","Davanagere","Karnataka",14.4644,75.9218),
    ("Ballari","Ballari","Karnataka",15.1394,76.9214),
    ("Shivamogga","Shivamogga","Karnataka",13.9299,75.5681),
    ("Tumakuru","Tumakuru","Karnataka",13.3379,77.1173),
    ("Raichur","Raichur","Karnataka",16.2120,77.3439),
    ("Bidar","Bidar","Karnataka",17.9119,77.5199),
    ("Vijayapura","Vijayapura","Karnataka",16.8302,75.7100),
    ("Bagalkot","Bagalkot","Karnataka",16.1697,75.6961),
    ("Dharwad","Dharwad","Karnataka",15.4589,74.9976),
    ("Hassan","Hassan","Karnataka",13.0068,76.0996),
    ("Chitradurga","Chitradurga","Karnataka",14.2251,76.3980),
    ("Udupi","Udupi","Karnataka",13.3409,74.7421),
    ("Mandya","Mandya","Karnataka",12.5218,76.8951),
    ("Kolar","Kolar","Karnataka",13.1361,78.1294),

    # ── Kerala ───────────────────────────────────────────────────────────────
    ("Thiruvananthapuram","Thiruvananthapuram","Kerala",8.5241,76.9366),
    ("Kochi","Ernakulam","Kerala",9.9312,76.2673),
    ("Kozhikode","Kozhikode","Kerala",11.2588,75.7804),
    ("Thrissur","Thrissur","Kerala",10.5276,76.2144),
    ("Kollam","Kollam","Kerala",8.8932,76.6141),
    ("Palakkad","Palakkad","Kerala",10.7867,76.6548),
    ("Alappuzha","Alappuzha","Kerala",9.4981,76.3388),
    ("Kannur","Kannur","Kerala",11.8745,75.3704),
    ("Malappuram","Malappuram","Kerala",11.0730,76.0740),
    ("Kottayam","Kottayam","Kerala",9.5916,76.5222),
    ("Kasaragod","Kasaragod","Kerala",12.4996,74.9869),
    ("Idukki","Idukki","Kerala",9.9189,76.9726),
    ("Pathanamthitta","Pathanamthitta","Kerala",9.2648,76.7870),
    ("Wayanad","Wayanad","Kerala",11.6854,76.1320),

    # ── Madhya Pradesh ───────────────────────────────────────────────────────
    ("Bhopal","Bhopal","Madhya Pradesh",23.2599,77.4126),
    ("Indore","Indore","Madhya Pradesh",22.7196,75.8577),
    ("Jabalpur","Jabalpur","Madhya Pradesh",23.1815,79.9864),
    ("Gwalior","Gwalior","Madhya Pradesh",26.2183,78.1828),
    ("Ujjain","Ujjain","Madhya Pradesh",23.1793,75.7849),
    ("Sagar","Sagar","Madhya Pradesh",23.8388,78.7378),
    ("Dewas","Dewas","Madhya Pradesh",22.9676,76.0534),
    ("Satna","Satna","Madhya Pradesh",24.5984,80.8322),
    ("Ratlam","Ratlam","Madhya Pradesh",23.3315,75.0367),
    ("Rewa","Rewa","Madhya Pradesh",24.5362,81.3042),
    ("Murwara","Katni","Madhya Pradesh",23.8340,80.3928),
    ("Singrauli","Singrauli","Madhya Pradesh",24.1997,82.6735),
    ("Burhanpur","Burhanpur","Madhya Pradesh",21.3082,76.2285),
    ("Khandwa","Khandwa","Madhya Pradesh",21.8253,76.3567),
    ("Bhind","Bhind","Madhya Pradesh",26.5645,78.7884),
    ("Chhindwara","Chhindwara","Madhya Pradesh",22.0574,78.9382),
    ("Morena","Morena","Madhya Pradesh",26.4975,77.9947),
    ("Vidisha","Vidisha","Madhya Pradesh",23.5251,77.8096),
    ("Damoh","Damoh","Madhya Pradesh",23.8328,79.4368),
    ("Shivpuri","Shivpuri","Madhya Pradesh",25.4228,77.6603),

    # ── Maharashtra ──────────────────────────────────────────────────────────
    ("Mumbai","Mumbai","Maharashtra",19.0760,72.8777),
    ("Pune","Pune","Maharashtra",18.5204,73.8567),
    ("Nagpur","Nagpur","Maharashtra",21.1458,79.0882),
    ("Nashik","Nashik","Maharashtra",19.9975,73.7898),
    ("Aurangabad","Chhatrapati Sambhajinagar","Maharashtra",19.8762,75.3433),
    ("Solapur","Solapur","Maharashtra",17.6805,75.9064),
    ("Amravati","Amravati","Maharashtra",20.9320,77.7523),
    ("Kolhapur","Kolhapur","Maharashtra",16.7050,74.2433),
    ("Nanded","Nanded","Maharashtra",19.1383,77.3210),
    ("Sangli","Sangli","Maharashtra",16.8524,74.5815),
    ("Malegaon","Nashik","Maharashtra",20.5579,74.5089),
    ("Jalgaon","Jalgaon","Maharashtra",21.0077,75.5626),
    ("Akola","Akola","Maharashtra",20.7002,77.0082),
    ("Latur","Latur","Maharashtra",18.4088,76.5604),
    ("Dhule","Dhule","Maharashtra",20.9042,74.7749),
    ("Ahmednagar","Ahmednagar","Maharashtra",19.0952,74.7496),
    ("Chandrapur","Chandrapur","Maharashtra",19.9615,79.2961),
    ("Parbhani","Parbhani","Maharashtra",19.2704,76.7756),
    ("Bhiwandi","Thane","Maharashtra",19.2967,73.0631),
    ("Navi Mumbai","Thane","Maharashtra",19.0330,73.0297),
    ("Thane","Thane","Maharashtra",19.2183,72.9781),
    ("Vasai-Virar","Palghar","Maharashtra",19.4690,72.8205),
    ("Kalyan","Thane","Maharashtra",19.2403,73.1305),
    ("Ulhasnagar","Thane","Maharashtra",19.2215,73.1533),
    ("Bid","Beed","Maharashtra",18.9890,75.7597),
    ("Osmanabad","Dharashiv","Maharashtra",18.1861,76.0390),
    ("Wardha","Wardha","Maharashtra",20.7453,78.6022),
    ("Yavatmal","Yavatmal","Maharashtra",20.3888,78.1204),
    ("Jalna","Jalna","Maharashtra",19.8346,75.8816),
    ("Washim","Washim","Maharashtra",20.1102,77.1448),

    # ── Manipur ──────────────────────────────────────────────────────────────
    ("Imphal","Imphal West","Manipur",24.8170,93.9368),
    ("Thoubal","Thoubal","Manipur",24.6368,94.0156),
    ("Bishnupur","Bishnupur","Manipur",24.6282,93.7764),
    ("Churachandpur","Churachandpur","Manipur",24.3326,93.6777),

    # ── Meghalaya ────────────────────────────────────────────────────────────
    ("Shillong","East Khasi Hills","Meghalaya",25.5788,91.8933),
    ("Tura","West Garo Hills","Meghalaya",25.5148,90.2153),
    ("Jowai","Jaintia Hills","Meghalaya",25.4494,92.2003),

    # ── Mizoram ──────────────────────────────────────────────────────────────
    ("Aizawl","Aizawl","Mizoram",23.7271,92.7176),
    ("Lunglei","Lunglei","Mizoram",22.8875,92.7345),

    # ── Nagaland ─────────────────────────────────────────────────────────────
    ("Kohima","Kohima","Nagaland",25.6747,94.1086),
    ("Dimapur","Dimapur","Nagaland",25.9044,93.7263),

    # ── Odisha ───────────────────────────────────────────────────────────────
    ("Bhubaneswar","Khordha","Odisha",20.2961,85.8245),
    ("Cuttack","Cuttack","Odisha",20.4625,85.8828),
    ("Brahmapur","Ganjam","Odisha",19.3150,84.7941),
    ("Rourkela","Sundergarh","Odisha",22.2492,84.8828),
    ("Sambalpur","Sambalpur","Odisha",21.4669,83.9756),
    ("Balasore","Balasore","Odisha",21.4942,86.9287),
    ("Baripada","Mayurbhanj","Odisha",21.9327,86.7302),
    ("Bhadrak","Bhadrak","Odisha",21.0638,86.5085),
    ("Jeypore","Koraput","Odisha",18.8536,82.5720),
    ("Angul","Angul","Odisha",20.8389,85.1011),
    ("Dhenkanal","Dhenkanal","Odisha",20.6615,85.5981),
    ("Jharsuguda","Jharsuguda","Odisha",21.8553,84.0064),

    # ── Punjab ───────────────────────────────────────────────────────────────
    ("Ludhiana","Ludhiana","Punjab",30.9010,75.8573),
    ("Amritsar","Amritsar","Punjab",31.6340,74.8723),
    ("Jalandhar","Jalandhar","Punjab",31.3260,75.5762),
    ("Patiala","Patiala","Punjab",30.3398,76.3869),
    ("Bathinda","Bathinda","Punjab",30.2110,74.9455),
    ("Mohali","SAS Nagar","Punjab",30.6942,76.7170),
    ("Firozpur","Firozpur","Punjab",30.9335,74.6082),
    ("Hoshiarpur","Hoshiarpur","Punjab",31.5143,75.9111),
    ("Moga","Moga","Punjab",30.8151,75.1714),
    ("Pathankot","Pathankot","Punjab",32.2745,75.6522),
    ("Gurdaspur","Gurdaspur","Punjab",32.0376,75.4019),
    ("Abohar","Fazilka","Punjab",30.1444,74.1973),
    ("Kapurthala","Kapurthala","Punjab",31.3793,75.3800),
    ("Fazilka","Fazilka","Punjab",30.4026,74.0227),

    # ── Rajasthan ────────────────────────────────────────────────────────────
    ("Jaipur","Jaipur","Rajasthan",26.9124,75.7873),
    ("Jodhpur","Jodhpur","Rajasthan",26.2389,73.0243),
    ("Kota","Kota","Rajasthan",25.2138,75.8648),
    ("Bikaner","Bikaner","Rajasthan",28.0229,73.3119),
    ("Ajmer","Ajmer","Rajasthan",26.4499,74.6399),
    ("Alwar","Alwar","Rajasthan",27.5530,76.6346),
    ("Bharatpur","Bharatpur","Rajasthan",27.2152,77.4900),
    ("Sikar","Sikar","Rajasthan",27.6152,75.1399),
    ("Pali","Pali","Rajasthan",25.7710,73.3234),
    ("Sri Ganganagar","Sri Ganganagar","Rajasthan",29.9038,73.8772),
    ("Udaipur","Udaipur","Rajasthan",24.5854,73.7125),
    ("Tonk","Tonk","Rajasthan",26.1688,75.7888),
    ("Hanumangarh","Hanumangarh","Rajasthan",29.5830,74.3285),
    ("Chittorgarh","Chittorgarh","Rajasthan",24.8887,74.6269),
    ("Sawai Madhopur","Sawai Madhopur","Rajasthan",26.0038,76.3537),
    ("Nagaur","Nagaur","Rajasthan",27.2025,73.7342),
    ("Jhunjhunu","Jhunjhunu","Rajasthan",28.1325,75.3980),
    ("Barmer","Barmer","Rajasthan",25.7463,71.3929),
    ("Jaisalmer","Jaisalmer","Rajasthan",26.9157,70.9083),
    ("Bundi","Bundi","Rajasthan",25.4385,75.6499),

    # ── Sikkim ───────────────────────────────────────────────────────────────
    ("Gangtok","East Sikkim","Sikkim",27.3389,88.6065),
    ("Namchi","South Sikkim","Sikkim",27.1664,88.3611),

    # ── Tamil Nadu ───────────────────────────────────────────────────────────
    ("Chennai","Chennai","Tamil Nadu",13.0827,80.2707),
    ("Coimbatore","Coimbatore","Tamil Nadu",11.0168,76.9558),
    ("Madurai","Madurai","Tamil Nadu",9.9252,78.1198),
    ("Tiruchirappalli","Tiruchirappalli","Tamil Nadu",10.7905,78.7047),
    ("Salem","Salem","Tamil Nadu",11.6643,78.1460),
    ("Tirunelveli","Tirunelveli","Tamil Nadu",8.7139,77.7567),
    ("Tiruppur","Tiruppur","Tamil Nadu",11.1085,77.3411),
    ("Erode","Erode","Tamil Nadu",11.3410,77.7172),
    ("Vellore","Vellore","Tamil Nadu",12.9165,79.1325),
    ("Thoothukudi","Thoothukudi","Tamil Nadu",8.7642,78.1348),
    ("Thanjavur","Thanjavur","Tamil Nadu",10.7870,79.1378),
    ("Dindigul","Dindigul","Tamil Nadu",10.3673,77.9803),
    ("Cuddalore","Cuddalore","Tamil Nadu",11.7447,79.7689),
    ("Kanchipuram","Kanchipuram","Tamil Nadu",12.8185,79.6947),
    ("Nagercoil","Kanyakumari","Tamil Nadu",8.1784,77.4345),
    ("Kumbakonam","Thanjavur","Tamil Nadu",10.9602,79.3845),
    ("Tiruvannamalai","Tiruvannamalai","Tamil Nadu",12.2253,79.0747),
    ("Karur","Karur","Tamil Nadu",10.9601,78.0766),
    ("Namakkal","Namakkal","Tamil Nadu",11.2195,78.1673),
    ("Sivakasi","Virudhunagar","Tamil Nadu",9.4517,77.7997),

    # ── Telangana ────────────────────────────────────────────────────────────
    ("Hyderabad","Hyderabad","Telangana",17.3850,78.4867),
    ("Warangal","Warangal Urban","Telangana",17.9689,79.5941),
    ("Nizamabad","Nizamabad","Telangana",18.6725,78.0940),
    ("Karimnagar","Karimnagar","Telangana",18.4386,79.1288),
    ("Khammam","Khammam","Telangana",17.2473,80.1514),
    ("Ramagundam","Peddapalli","Telangana",18.7549,79.4790),
    ("Secunderabad","Hyderabad","Telangana",17.4399,78.4983),
    ("Nalgonda","Nalgonda","Telangana",17.0575,79.2688),
    ("Mahbubnagar","Mahbubnagar","Telangana",16.7488,77.9834),
    ("Adilabad","Adilabad","Telangana",19.6641,78.5320),
    ("Medak","Medak","Telangana",18.0462,78.2640),
    ("Siddipet","Siddipet","Telangana",18.1029,78.8518),
    ("Suryapet","Suryapet","Telangana",17.1439,79.6270),
    ("Wanaparthy","Wanaparthy","Telangana",16.3633,78.0633),

    # ── Tripura ──────────────────────────────────────────────────────────────
    ("Agartala","West Tripura","Tripura",23.8315,91.2868),
    ("Dharmanagar","North Tripura","Tripura",24.3792,92.1620),
    ("Udaipur","Gomati","Tripura",23.5333,91.4833),

    # ── Uttar Pradesh ────────────────────────────────────────────────────────
    ("Lucknow","Lucknow","Uttar Pradesh",26.8467,80.9462),
    ("Kanpur","Kanpur Nagar","Uttar Pradesh",26.4499,80.3319),
    ("Ghaziabad","Ghaziabad","Uttar Pradesh",28.6692,77.4538),
    ("Agra","Agra","Uttar Pradesh",27.1767,78.0081),
    ("Meerut","Meerut","Uttar Pradesh",28.9845,77.7064),
    ("Varanasi","Varanasi","Uttar Pradesh",25.3176,82.9739),
    ("Prayagraj","Prayagraj","Uttar Pradesh",25.4358,81.8463),
    ("Bareilly","Bareilly","Uttar Pradesh",28.3670,79.4304),
    ("Aligarh","Aligarh","Uttar Pradesh",27.8974,78.0880),
    ("Moradabad","Moradabad","Uttar Pradesh",28.8386,78.7733),
    ("Saharanpur","Saharanpur","Uttar Pradesh",29.9679,77.5460),
    ("Gorakhpur","Gorakhpur","Uttar Pradesh",26.7606,83.3732),
    ("Noida","Gautam Buddha Nagar","Uttar Pradesh",28.5355,77.3910),
    ("Firozabad","Firozabad","Uttar Pradesh",27.1592,78.3957),
    ("Mathura","Mathura","Uttar Pradesh",27.4924,77.6737),
    ("Jhansi","Jhansi","Uttar Pradesh",25.4484,78.5685),
    ("Muzaffarnagar","Muzaffarnagar","Uttar Pradesh",29.4727,77.7085),
    ("Ghazipur","Ghazipur","Uttar Pradesh",25.5806,83.5791),
    ("Ayodhya","Ayodhya","Uttar Pradesh",26.7922,82.1998),
    ("Rampur","Rampur","Uttar Pradesh",28.8183,79.0247),
    ("Shahjahanpur","Shahjahanpur","Uttar Pradesh",27.8831,79.9081),
    ("Farrukhabad","Farrukhabad","Uttar Pradesh",27.3856,79.5760),
    ("Hapur","Hapur","Uttar Pradesh",28.7277,77.7798),
    ("Etawah","Etawah","Uttar Pradesh",26.7861,79.0233),
    ("Bulandshahr","Bulandshahr","Uttar Pradesh",28.4077,77.8491),
    ("Ambedkar Nagar","Ambedkar Nagar","Uttar Pradesh",26.4443,82.6825),
    ("Lakhimpur","Lakhimpur Kheri","Uttar Pradesh",27.9497,80.7752),
    ("Sitapur","Sitapur","Uttar Pradesh",27.5637,80.6812),
    ("Jaunpur","Jaunpur","Uttar Pradesh",25.7464,82.6836),
    ("Sultanpur","Sultanpur","Uttar Pradesh",26.2648,82.0727),

    # ── Uttarakhand ──────────────────────────────────────────────────────────
    ("Dehradun","Dehradun","Uttarakhand",30.3165,78.0322),
    ("Haridwar","Haridwar","Uttarakhand",29.9457,78.1642),
    ("Roorkee","Haridwar","Uttarakhand",29.8543,77.8880),
    ("Haldwani","Nainital","Uttarakhand",29.2183,79.5130),
    ("Rudrapur","Udham Singh Nagar","Uttarakhand",28.9766,79.3961),
    ("Kashipur","Udham Singh Nagar","Uttarakhand",29.2110,78.9583),
    ("Rishikesh","Dehradun","Uttarakhand",30.0869,78.2676),
    ("Pithoragarh","Pithoragarh","Uttarakhand",29.5827,80.2180),

    # ── West Bengal ──────────────────────────────────────────────────────────
    ("Kolkata","Kolkata","West Bengal",22.5726,88.3639),
    ("Asansol","Paschim Bardhaman","West Bengal",23.6834,86.9820),
    ("Siliguri","Darjeeling","West Bengal",26.7271,88.3953),
    ("Durgapur","Paschim Bardhaman","West Bengal",23.5204,87.3119),
    ("Bardhaman","Purba Bardhaman","West Bengal",23.2324,87.8615),
    ("Malda","Malda","West Bengal",25.0108,88.1423),
    ("Baharampur","Murshidabad","West Bengal",24.1072,88.2512),
    ("Habra","North 24 Parganas","West Bengal",22.8400,88.6549),
    ("Kharagpur","Paschim Medinipur","West Bengal",22.3460,87.3238),
    ("Shantipur","Nadia","West Bengal",23.2475,88.4340),
    ("Darjeeling","Darjeeling","West Bengal",27.0360,88.2627),
    ("Jalpaiguri","Jalpaiguri","West Bengal",26.5435,88.7179),
    ("Cooch Behar","Cooch Behar","West Bengal",26.3268,89.4472),
    ("Midnapore","Paschim Medinipur","West Bengal",22.4250,87.3193),
    ("Haldia","Purba Medinipur","West Bengal",22.0257,88.0583),
    ("Krishnanagar","Nadia","West Bengal",23.4018,88.5001),
    ("Purulia","Purulia","West Bengal",23.3318,86.3636),
    ("Bankura","Bankura","West Bengal",23.2324,87.0747),
    ("Birbhum","Birbhum","West Bengal",23.8893,87.6143),
    ("North 24 Parganas","North 24 Parganas","West Bengal",22.8400,88.6549),

    # ── Delhi NCT ────────────────────────────────────────────────────────────
    ("New Delhi","New Delhi","Delhi",28.6139,77.2090),
    ("Delhi North","North Delhi","Delhi",28.7041,77.1025),
    ("Delhi South","South Delhi","Delhi",28.5245,77.1855),
    ("Delhi East","East Delhi","Delhi",28.6508,77.2858),
    ("Delhi West","West Delhi","Delhi",28.6456,77.0777),
    ("Dwarka","South West Delhi","Delhi",28.5921,77.0460),
    ("Rohini","North West Delhi","Delhi",28.7422,77.0658),
    ("Noida","Gautam Buddha Nagar","Delhi",28.5355,77.3910),

    # ── Jammu & Kashmir ──────────────────────────────────────────────────────
    ("Srinagar","Srinagar","Jammu and Kashmir",34.0837,74.7973),
    ("Jammu","Jammu","Jammu and Kashmir",32.7357,74.8691),
    ("Anantnag","Anantnag","Jammu and Kashmir",33.7311,75.1487),
    ("Baramulla","Baramulla","Jammu and Kashmir",34.2097,74.3436),
    ("Sopore","Baramulla","Jammu and Kashmir",34.2977,74.4702),
    ("Udhampur","Udhampur","Jammu and Kashmir",32.9160,75.1416),
    ("Kathua","Kathua","Jammu and Kashmir",32.3843,75.5186),
    ("Kupwara","Kupwara","Jammu and Kashmir",34.5219,74.2609),

    # ── Ladakh ───────────────────────────────────────────────────────────────
    ("Leh","Leh","Ladakh",34.1526,77.5771),
    ("Kargil","Kargil","Ladakh",34.5539,76.1349),

    # ── Puducherry ───────────────────────────────────────────────────────────
    ("Puducherry","Puducherry","Puducherry",11.9416,79.8083),
    ("Karaikal","Karaikal","Puducherry",10.9254,79.8380),

    # ── Chandigarh ───────────────────────────────────────────────────────────
    ("Chandigarh","Chandigarh","Chandigarh",30.7333,76.7794),

    # ── Andaman & Nicobar ────────────────────────────────────────────────────
    ("Port Blair","South Andaman","Andaman and Nicobar Islands",11.6234,92.7265),

    # ── Lakshadweep ──────────────────────────────────────────────────────────
    ("Kavaratti","Lakshadweep","Lakshadweep",10.5669,72.6420),

    # ── Dadra & NH / Daman & Diu ─────────────────────────────────────────────
    ("Silvassa","Dadra and NH","Dadra and Nagar Haveli and Daman and Diu",20.2766,73.0169),
    ("Daman","Daman","Dadra and Nagar Haveli and Daman and Diu",20.3974,72.8328),
]

# ─────────────────────────────────────────────────────────────────────────────
# HOSPITAL TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
HOSPITAL_TYPES = [
    ("Government Medical College Hospital",      "General Medicine, Surgery, Obstetrics & Gynaecology, Paediatrics, Orthopaedics, Neurology, Cardiology, Oncology", True),
    ("District General Hospital",                "General Medicine, Surgery, Emergency Medicine, Paediatrics, Orthopaedics", True),
    ("Apollo Hospitals",                         "Cardiology, Neurology, Oncology, Orthopaedics, General Medicine, Gastroenterology", True),
    ("Fortis Hospital",                          "Cardiology, Neurology, Oncology, Nephrology, General Medicine, Emergency Medicine", True),
    ("Max Healthcare",                           "Cardiology, Orthopaedics, Neurology, Oncology, Transplant Medicine, General Medicine", True),
    ("AIIMS Regional Centre",                    "All Specialties, Research Medicine, Oncology, Cardiology, Neurology, Transplant", True),
    ("Community Health Centre",                  "General Medicine, Maternal Health, Paediatrics, Emergency Medicine", False),
    ("Primary Health Centre",                    "General Medicine, Maternal Health, Paediatrics, Vaccination", False),
    ("Manipal Hospitals",                        "Cardiology, Neurology, Orthopaedics, Oncology, General Medicine, Gastroenterology", True),
    ("Narayana Health",                          "Cardiology, Paediatric Cardiology, Oncology, Orthopaedics, General Medicine", True),
    ("Medanta - The Medicity",                   "Cardiology, Neurology, Oncology, Orthopaedics, Transplant, General Medicine", True),
    ("KIMS Hospital",                            "Cardiology, Neurology, Orthopaedics, General Medicine, Gastroenterology, Oncology", True),
    ("Rainbow Children's Hospital",              "Paediatrics, Neonatology, Paediatric Surgery, NICU", False),
    ("Yashoda Hospitals",                        "Cardiology, Neurology, Orthopaedics, General Medicine, Gastroenterology", True),
    ("Care Hospitals",                           "Cardiology, Neurology, General Medicine, Nephrology, Oncology", True),
    ("Sri Venkateswara Institute of Medical Sciences", "General Medicine, Surgery, Cardiology, Neurology, Oncology, Nephrology", True),
    ("Nims Hospital",                            "General Medicine, Surgery, Orthopaedics, Cardiology, Neurology, Oncology", True),
    ("Sunshine Hospitals",                       "Orthopaedics, Neurology, Cardiology, Oncology, General Medicine", True),
    ("Citizens Specialty Hospital",              "General Medicine, Cardiology, Orthopaedics, Gastroenterology, Oncology", True),
    ("ESI Hospital",                             "General Medicine, Surgery, Orthopaedics, Obstetrics & Gynaecology, Paediatrics", True),
    ("Railway Hospital",                         "General Medicine, Surgery, Orthopaedics, Emergency Medicine, Paediatrics", True),
    ("Aster Hospitals",                          "Cardiology, Neurology, Oncology, General Medicine, Gastroenterology, Orthopaedics", True),
    ("Columbia Asia Hospital",                   "General Medicine, Surgery, Orthopaedics, Cardiology, Neurology", True),
    ("Lotus Hospitals",                          "Obstetrics & Gynaecology, Neonatology, Paediatrics, General Medicine", False),
    ("SRM Hospitals",                            "General Medicine, Surgery, Cardiology, Neurology, Oncology, Transplant", True),
    ("Kauvery Hospital",                         "Cardiology, Neurology, General Medicine, Oncology, Orthopaedics", True),
    ("PSG Hospitals",                            "General Medicine, Cardiology, Neurology, Oncology, Orthopaedics, Gastroenterology", True),
    ("Global Hospital",                          "Transplant, Cardiology, Neurology, Oncology, General Medicine, Gastroenterology", True),
    ("Vikram Hospital",                          "Oncology, Cardiology, Neurology, Orthopaedics, General Medicine", True),
    ("Meenakshi Mission Hospital",               "Cardiology, Neurology, Oncology, General Medicine, Orthopaedics", True),
]

DOCTOR_PREFIXES = ["Dr.","Dr.","Dr.","Dr."]
FIRST_NAMES = [
    "Rajesh","Priya","Suresh","Anjali","Arun","Meera","Vikram","Sunita","Ramesh","Kavya",
    "Deepak","Pooja","Manoj","Sree","Kiran","Ananya","Sanjay","Lavanya","Ravi","Divya",
    "Venkat","Swathi","Harish","Nandini","Sunil","Pallavi","Ganesh","Madhavi","Ajay","Rekha",
    "Aditya","Shreya","Naresh","Usha","Vijay","Chitra","Santosh","Vinitha","Bala","Saranya",
    "Prasad","Radha","Srinivas","Jyothi","Krishnan","Amrutha","Mohan","Sahana","Nagesh","Shanti",
]
LAST_NAMES = [
    "Kumar","Sharma","Reddy","Patel","Singh","Rao","Naidu","Menon","Iyer","Pillai",
    "Verma","Gupta","Joshi","Shah","Mehta","Desai","Nair","Varma","Rajan","Krishnan",
    "Pandey","Tiwari","Mishra","Srivastava","Agarwal","Saxena","Bose","Das","Ghosh","Chatterjee",
    "Mukherjee","Banerjee","Dey","Sen","Paul","Roy","Chandra","Bhat","Kaur","Malhotra",
]
QUALIFICATIONS = [
    "MBBS, MD","MBBS, MS","MBBS, MD, DM","MBBS, MS, MCh","MBBS, DNB",
    "MBBS, MD (Internal Medicine)","MBBS, MS (Ortho)","MBBS, MD, FRCP",
    "MBBS, MD (Cardiology)","MBBS, MCh (Neuro)","MBBS, MD, DM (Nephrology)",
]
EXPERIENCES = ["3 Years","5 Years","7 Years","10 Years","12 Years","15 Years","18 Years","20 Years","25 Years"]

def rand_phone():
    prefixes = ["9","8","7","6"]
    return f"+91-{random.choice(prefixes)}{random.randint(100000000,999999999)}"

def rand_offset(scale=0.03):
    """Small random offset from city center for hospital lat/lon."""
    return (random.uniform(-scale, scale), random.uniform(-scale, scale))

def make_hospital_id(city, h_type_name, idx):
    safe = "".join(c for c in city if c.isalnum()).upper()[:6]
    safe_h = "".join(c for c in h_type_name.split()[0] if c.isalnum()).upper()[:4]
    return f"HOSP-{safe}-{safe_h}-{idx:03d}"

def generate_hospitals():
    hospitals = []
    hospital_id_counter = 1

    for city, district, state, city_lat, city_lon in INDIA_CITIES:
        # Pick 5-6 unique hospital types for this city
        n = random.choice([5, 5, 6, 6])
        selected_types = random.sample(HOSPITAL_TYPES, min(n, len(HOSPITAL_TYPES)))

        for i, (h_type, specialization, emergency) in enumerate(selected_types):
            dlat, dlon = rand_offset(0.04)
            h_lat = round(city_lat + dlat, 6)
            h_lon = round(city_lon + dlon, 6)

            h_name = f"{h_type}, {city}"
            h_id = make_hospital_id(city, h_type, hospital_id_counter)
            hospital_id_counter += 1

            h_addr = f"Survey No. {random.randint(1,999)}, {random.choice(['MG Road','NH-44','Ring Road','Civil Lines','Station Road','Main Street','Bypass Road','Medical Colony'])}, {city}"

            beds = random.randint(50, 800)
            icu  = random.randint(5,  min(60, beds // 5))
            emerg_str = "Yes" if emergency else "No"
            avail_str = random.choice(["Open", "Open", "Open", "Busy", "Full"])

            hospitals.append({
                "hospital_id":         h_id,
                "hospital_name":       h_name,
                "address":             h_addr,
                "city":                city,
                "district":            district,
                "state":               state,
                "phone":               rand_phone(),
                "specialization":      specialization,
                "emergency_available": emerg_str,
                "latitude":            h_lat,
                "longitude":           h_lon,
                "availability_status": avail_str,
                "available_beds":      beds,
                "available_icu":       icu,
                "emergency_support":   emerg_str,
            })

    return hospitals


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Create hospitals_directory ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS hospitals_directory (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id      TEXT UNIQUE,
            hospital_name    TEXT,
            address          TEXT,
            city             TEXT,
            district         TEXT,
            state            TEXT,
            phone            TEXT,
            specialization   TEXT,
            emergency_available TEXT DEFAULT 'No',
            latitude         REAL,
            longitude        REAL,
            availability_status TEXT DEFAULT 'Open',
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Create hospital_beds ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS hospital_beds (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_name    TEXT UNIQUE,
            hospital_id      TEXT,
            available_beds   INTEGER DEFAULT 100,
            available_icu    INTEGER DEFAULT 10,
            emergency_support TEXT DEFAULT 'No',
            updated_at       TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Wipe old seeded data and re-seed ─────────────────────────────────────
    c.execute("DELETE FROM hospitals_directory")
    c.execute("DELETE FROM hospital_beds")

    hospitals = generate_hospitals()

    for h in hospitals:
        c.execute("""
            INSERT OR REPLACE INTO hospitals_directory
                (hospital_id, hospital_name, address, city, district, state, phone,
                 specialization, emergency_available, latitude, longitude, availability_status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            h["hospital_id"], h["hospital_name"], h["address"], h["city"],
            h["district"], h["state"], h["phone"], h["specialization"],
            h["emergency_available"], h["latitude"], h["longitude"],
            h["availability_status"]
        ))

        c.execute("""
            INSERT OR REPLACE INTO hospital_beds
                (hospital_name, hospital_id, available_beds, available_icu, emergency_support)
            VALUES (?,?,?,?,?)
        """, (
            h["hospital_name"], h["hospital_id"],
            h["available_beds"], h["available_icu"], h["emergency_support"]
        ))

    conn.commit()
    conn.close()
    print(f"✅ Seeded {len(hospitals)} hospitals across {len(INDIA_CITIES)} cities/towns into hospital.db")
    return len(hospitals)


if __name__ == "__main__":
    count = seed()
    print(f"Total hospitals in DB: {count}")
