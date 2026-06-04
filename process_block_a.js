const fs = require('fs');
const path = require('path');

// 1. Parser thủ công tệp .env để lấy cấu hình CSDL
function loadEnv() {
    const envPath = path.resolve(__dirname, '.env');
    const env = {};
    if (fs.existsSync(envPath)) {
        const content = fs.readFileSync(envPath, 'utf8');
        content.split(/\r?\n/).forEach(line => {
            const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
            if (match) {
                const key = match[1];
                let value = match[2] || '';
                if (value.length > 0 && value.charAt(0) === '"' && value.charAt(value.length - 1) === '"') {
                    value = value.substring(1, value.length - 1);
                } else if (value.length > 0 && value.charAt(0) === "'" && value.charAt(value.length - 1) === "'") {
                    value = value.substring(1, value.length - 1);
                }
                env[key] = value.trim();
            }
        });
    }
    return env;
}

const env = loadEnv();

// 2. Import thư viện mysql2
let mysql;
try {
    mysql = require('mysql2/promise');
} catch (e) {
    console.error('\x1b[31m[LỖI] Gói "mysql2" chưa được cài đặt.\x1b[0m');
    console.error('Vui lòng chạy lệnh sau để cài đặt thư viện trước khi chạy script này:');
    console.error('\x1b[36m    npm install mysql2\x1b[0m\n');
    process.exit(1);
}

async function main() {
    const dbConfig = {
        host: env.DB_HOST || 'localhost',
        user: env.DB_USER || 'root',
        password: env.DB_PASSWORD || '',
        database: env.DB_NAME || 'optidut_db',
        port: parseInt(env.DB_PORT || '3306')
    };

    console.log('\x1b[36m%s\x1b[0m', '══════════════════════════════════════════════════════════');
    console.log('\x1b[36m%s\x1b[0m', '  HỆ THỐNG XÓA HOÀN TOÀN KHU HÀNH CHÍNH A - OPTIDUT');
    console.log('\x1b[36m%s\x1b[0m', '══════════════════════════════════════════════════════════');
    console.log(`Đang kết nối tới CSDL MySQL: ${dbConfig.user}@${dbConfig.host}:${dbConfig.port}/${dbConfig.database}...`);

    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        console.log('\x1b[32m✔ Kết nối thành công!\x1b[0m\n');
    } catch (err) {
        console.error('\x1b[31m❌ Lỗi kết nối CSDL:\x1b[0m', err.message);
        console.log('\nVui lòng kiểm tra lại cấu hình trong tệp \x1b[33m.env\x1b[0m.');
        process.exit(1);
    }

    try {
        // Quét lấy ID của tất cả phòng thuộc Khu A
        console.log('Đang quét danh sách phòng học thuộc Khu A...');
        const [rooms] = await connection.query(
            "SELECT id, ma_phong FROM phong_hoc WHERE toa_nha LIKE '%Tòa A%' OR toa_nha LIKE '%Khu A%' OR ma_phong LIKE 'A%'"
        );

        if (rooms.length === 0) {
            console.log('\x1b[32m✔ Không tìm thấy phòng học nào thuộc Khu A trong CSDL. Quá trình hoàn tất!\x1b[0m');
            await connection.end();
            return;
        }

        const roomIds = rooms.map(r => r.id);
        console.log(`Tìm thấy \x1b[36m${rooms.length}\x1b[0m phòng thuộc Khu A.`);
        console.log('Bắt đầu xóa dọn dẹp các liên kết khóa ngoại và xóa phòng học...\n');

        // 1. Xóa các yêu cầu đổi phòng học liên quan đến phòng mới ở Khu A
        const [resYcNewRoom] = await connection.query(
            "DELETE FROM yeu_cau_doi_lich WHERE phong_moi_id IN (?)", [roomIds]
        );
        console.log(`  - Đã xóa \x1b[33m${resYcNewRoom.affectedRows}\x1b[0m yêu cầu đổi phòng liên quan đến Khu A.`);

        // 2. Xóa các yêu cầu đổi lịch liên quan đến lịch học ở Khu A
        const [resYcLich] = await connection.query(
            "DELETE FROM yeu_cau_doi_lich WHERE lich_hoc_id IN (SELECT id FROM lich_hoc WHERE phong_hoc_id IN (?))", [roomIds]
        );
        console.log(`  - Đã xóa \x1b[33m${resYcLich.affectedRows}\x1b[0m yêu cầu đổi lịch học (tiết học tại Khu A).`);

        // 3. Xóa các báo hỏng thiết bị liên quan đến thiết bị lắp đặt ở Khu A
        const [resBaoHong] = await connection.query(
            "DELETE FROM bao_hong WHERE thiet_bi_id IN (SELECT id FROM thiet_bi WHERE phong_hoc_id IN (?))", [roomIds]
        );
        console.log(`  - Đã xóa \x1b[33m${resBaoHong.affectedRows}\x1b[0m báo cáo sự cố thiết bị tại Khu A.`);

        // 4. Xóa thiết bị lắp đặt tại các phòng thuộc Khu A
        const [resThietBi] = await connection.query(
            "DELETE FROM thiet_bi WHERE phong_hoc_id IN (?)", [roomIds]
        );
        console.log(`  - Đã xóa \x1b[33m${resThietBi.affectedRows}\x1b[0m thiết bị tại các phòng học Khu A.`);

        // 5. Xóa toàn bộ lịch dạy/lịch học phân bổ tại các phòng thuộc Khu A
        const [resLich] = await connection.query(
            "DELETE FROM lich_hoc WHERE phong_hoc_id IN (?)", [roomIds]
        );
        console.log(`  - Đã xóa \x1b[33m${resLich.affectedRows}\x1b[0m lịch học phân bổ tại Khu A.`);

        // 6. Xóa toàn bộ phòng thuộc Khu A khỏi bảng phong_hoc
        const [resRooms] = await connection.query(
            "DELETE FROM phong_hoc WHERE id IN (?)", [roomIds]
        );
        console.log(`\n  \x1b[31m✔ THÀNH CÔNG: ĐÃ XÓA HOÀN TOÀN ${resRooms.affectedRows} phòng thuộc Khu A khỏi cơ sở dữ liệu.\x1b[0m`);

        console.log('\n\x1b[36m%s\x1b[0m', '══════════════════════════════════════════════════════════');
        console.log('\x1b[32m%s\x1b[0m', '  ĐÃ XÓA TRIỆT ĐỂ TOÀN BỘ KHU HÀNH CHÍNH A KHỎI HỆ THỐNG!');
        console.log('\x1b[36m%s\x1b[0m', '══════════════════════════════════════════════════════════');

    } catch (err) {
        console.error('\x1b[31m[LỖI HỆ THỐNG]\x1b[0m', err.message);
    } finally {
        await connection.end();
        console.log('Đã đóng kết nối cơ sở dữ liệu.');
    }
}

main();
