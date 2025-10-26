"""shorten_long_translations

Revision ID: c68a4d210c35
Revises: 3207794d8134
Create Date: 2025-10-26 19:15:58.244125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c68a4d210c35'
down_revision: Union[str, None] = '3207794d8134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Shorten long MCC translations to under 100 characters."""
    # MCC 1740 UK: 164 -> 75 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Ізоляція, Штукатурні роботи - Підрядники' 
        WHERE mcc_code = 1740 AND lang = 'uk';
    """)
    
    # MCC 1740 RU: 157 -> 67 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Изоляция, Каменщики, Каменная кладка, Штукатурные работы - Подрядчики' 
        WHERE mcc_code = 1740 AND lang = 'ru';
    """)
    
    # MCC 5961 UK: 159 -> 72 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Магазини поштових замовлень, книжкові/звукозаписні клуби' 
        WHERE mcc_code = 5961 AND lang = 'uk';
    """)
    
    # MCC 5961 RU: 145 -> 52 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Дома заказов по почте, книжные/рекордные клубы' 
        WHERE mcc_code = 5961 AND lang = 'ru';
    """)
    
    # MCC 4214 UK: 152 -> 73 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Автомобільні вантажоперевізники, переїзди, зберігання, доставка' 
        WHERE mcc_code = 4214 AND lang = 'uk';
    """)
    
    # MCC 4214 RU: 125 -> 60 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Автомобильные грузоперевозчики, переезды, хранение, доставка' 
        WHERE mcc_code = 4214 AND lang = 'ru';
    """)
    
    # MCC 1711 UK: 123 -> 64 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Кондиціонування, опалення - Підрядники: продаж, обслуговування' 
        WHERE mcc_code = 1711 AND lang = 'uk';
    """)
    
    # MCC 1711 RU: 121 -> 62 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Кондиционирование, отопление - Подрядчики: продажа, обслуживание' 
        WHERE mcc_code = 1711 AND lang = 'ru';
    """)
    
    # MCC 5511 UK: 114 -> 92 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Дилеры легковых и грузовых автомобилей: продажа, обслуживание, ремонт, запчасти' 
        WHERE mcc_code = 5511 AND lang = 'uk';
    """)
    
    # MCC 5511 RU: 109 -> 95 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Дилеры легковых и грузовых автомобилей: продажа, обслуживание' 
        WHERE mcc_code = 5511 AND lang = 'ru';
    """)
    
    # MCC 7995 UK: 110 -> 58 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Ставки - лотерея, казино, поза треком, іподроми' 
        WHERE mcc_code = 7995 AND lang = 'uk';
    """)
    
    # MCC 7995 RU: 101 -> 55 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Ставки - лотерея, казино, вне ипподрома, ипподромы' 
        WHERE mcc_code = 7995 AND lang = 'ru';
    """)
    
    # MCC 7011 RU: 107 -> 70 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Жилье - гостиницы, мотели, курорты, службы бронирования' 
        WHERE mcc_code = 7011 AND lang = 'ru';
    """)
    
    # MCC 4111 RU: 107 -> 70 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Местные/пригородные пассажирские перевозки - железные дороги, паромы' 
        WHERE mcc_code = 4111 AND lang = 'ru';
    """)
    
    # MCC 6399 RU: 105 -> 64 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Страхование, не классифицируемое в других рубриках' 
        WHERE mcc_code = 6399 AND lang = 'ru';
    """)
    
    # MCC 1761 UK: 105 -> 65 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Покрівельні роботи - підрядники, Роботи з листового металу, Сайдинг' 
        WHERE mcc_code = 1761 AND lang = 'uk';
    """)
    
    # MCC 6051 RU: 103 -> 72 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Нефинансовые учреждения - валюта, денежные переводы, дорожные чеки' 
        WHERE mcc_code = 6051 AND lang = 'ru';
    """)
    
    # MCC 5499 RU: 101 -> 72 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Продовольственные магазины - товары повседневного спроса и рынки' 
        WHERE mcc_code = 5499 AND lang = 'ru';
    """)
    
    # MCC 5813 RU: 101 -> 61 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Бары, Таверны, Коктейльные салоны, Ночные клубы, Дискотеки' 
        WHERE mcc_code = 5813 AND lang = 'ru';
    """)
    
    # MCC 7997 RU: 100 -> 78 chars
    op.execute("""
        UPDATE translations 
        SET text = 'Членские клубы (спортивные, рекреационные), загородные клубы, гольф' 
        WHERE mcc_code = 7997 AND lang = 'ru';
    """)

def downgrade() -> None:
    """Restore original long MCC translations."""
    op.execute("""
        UPDATE translations 
        SET text = 'Ізоляція - Підрядники, Кладка, Підрядники з мурування, Підрядники з кладки, Підрядники з штукатурки, Підрядники з мурування та кладки, Підрядники з укладання плитки' 
        WHERE mcc_code = 1740 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Изоляция - Подрядчики, Каменщики, Подрядчики каменной кладки, Подрядчики штукатурных работ, Подрядчики каменной кладки и кладки, Подрядчики по укладке плитки' 
        WHERE mcc_code = 1740 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Магазини поштових замовлень, включаючи магазини замовлень за каталогом, книжкові/звукозаписні клуби (більше не дозволяється для оригінальних презентацій у США)' 
        WHERE mcc_code = 5961 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Дома заказов по почте, включая магазины заказов по каталогу, книжные/рекордные клубы (больше не допускается для оригиналов, представленных в США)' 
        WHERE mcc_code = 5961 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Автомобільні вантажні перевізники, компанії, що займаються переїздами та зберіганням, вантажоперевезення - місцеві/міжміські, послуги доставки - місцеві' 
        WHERE mcc_code = 4214 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Автомобильные грузоперевозчики, Компании по переездам и хранению, Грузоперевозки - местные/дальние, Службы доставки - местные' 
        WHERE mcc_code = 4214 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Підрядники з кондиціонування повітря - продаж та встановлення, Підрядники з опалення - продаж, обслуговування, встановлення' 
        WHERE mcc_code = 1711 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Подрядчики по кондиционированию воздуха - продажа и установка, Подрядчики по отоплению - продажа, обслуживание, установка' 
        WHERE mcc_code = 1711 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Дилери легкових та вантажних автомобілів (нових та вживаних): продаж, обслуговування, ремонт, запчастини та лізинг' 
        WHERE mcc_code = 5511 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Дилеры легковых и грузовых автомобилей (новых и подержанных) Продажа, обслуживание, ремонт, запчасти и лизинг' 
        WHERE mcc_code = 5511 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Ставки (включно з лотерейними квитками, ігровими фішками казино, ставками поза треком і ставками на іподромах)' 
        WHERE mcc_code = 7995 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Ставки (включая лотерейные билеты, игровые фишки казино, ставки вне ипподрома и ставки на ипподромах)' 
        WHERE mcc_code = 7995 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Жилье - гостиницы, мотели, курорты, центральные службы бронирования (не классифицируется в других рубриках)' 
        WHERE mcc_code = 7011 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Местные/пригородные пригородные пассажирские перевозки - железные дороги, паромы, местные водные перевозки.' 
        WHERE mcc_code = 4111 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Страхование, не классифицируемое в других рубриках (больше не действует для работ с первым предъявлением)' 
        WHERE mcc_code = 6399 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Покрівельні роботи - підрядники, Покрівельні роботи з листового металу - підрядники, Сайдинг - підрядники' 
        WHERE mcc_code = 1761 AND lang = 'uk';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Нефинансовые учреждения - иностранная валюта, денежные переводы (не банковский перевод) и дорожные чеки' 
        WHERE mcc_code = 6051 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Разное. Продовольственные магазины - магазины товаров повседневного спроса и специализированные рынки' 
        WHERE mcc_code = 5499 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Питейные заведения (Алкогольные напитки), Бары, Таверны, Коктейльные салоны, Ночные клубы и Дискотеки' 
        WHERE mcc_code = 5813 AND lang = 'ru';
    """)
    
    op.execute("""
        UPDATE translations 
        SET text = 'Членские клубы (спортивные, рекреационные, атлетические), загородные клубы и частные поля для гольфа' 
        WHERE mcc_code = 7997 AND lang = 'ru';
    """)
