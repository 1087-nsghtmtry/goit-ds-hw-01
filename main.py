from collections import UserDict
from datetime import datetime, date, timedelta
import pickle

ADDRESS_FILE = "addressbook.pkl" 

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value: str):
        value = str(value).strip()
        if not value:
            raise ValueError("Задайте ім'я")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value: str):
        value = str(value).strip()
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Номер має містити 10 цифр")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        value = str(value).strip()
        try:
            parsed_value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Невірний формат дати, має бути: DD.MM.YYYY")

        super().__init__(parsed_value.strftime("%d.%m.%Y"))

    @property
    def date_value(self) -> date:
        return datetime.strptime(self.value, "%d.%m.%Y").date()


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone: str):
        self.phones.append(Phone(phone))

    def find_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def edit_phone(self, old_phone: str, new_phone: str):
        p = self.find_phone(old_phone)
        if p is None:
            raise ValueError(f"Old phone {old_phone} not found")
        p.value = Phone(new_phone).value

    def remove_phone(self, phone: str):
        p = self.find_phone(phone)
        if p is None:
            raise ValueError("Nothing to remove")
        self.phones.remove(p)

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = " ; ".join(p.value for p in self.phones) if self.phones else "-"
        bday_str = self.birthday.value if self.birthday else "-"
        return f"{self.name.value}, phones: {phones_str}, birthday: {bday_str}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str):
        if name not in self.data:
            raise KeyError("Name not found")
        return self.data.pop(name)

    def __str__(self):
        if not self.data:
            return "[]"
        return "\n".join(str(record) for record in self.data.values())

    def _safe_birthday_for_year(self, bday: date, year: int) -> date:
        try:
            return bday.replace(year=year)
        except ValueError:
            return date(year, 2, 28)

    def get_upcoming_birthdays(self, days: int = 7):
        upcoming = []
        today = date.today()

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday_date: date = record.birthday.date_value
            birthday_this_year = self._safe_birthday_for_year(bday_date, today.year)

            if birthday_this_year < today:
                birthday_this_year = self._safe_birthday_for_year(bday_date, today.year + 1)

            if birthday_this_year.weekday() == 5:      # субота
                congrat_date = birthday_this_year + timedelta(days=2)
            elif birthday_this_year.weekday() == 6:    # неділя
                congrat_date = birthday_this_year + timedelta(days=1)
            else:
                congrat_date = birthday_this_year

            delta = (congrat_date - today).days
            if 0 <= delta <= days:
                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congrat_date.strftime("%d.%m.%Y")
                })

        upcoming.sort(key=lambda x: datetime.strptime(x["congratulation_date"], "%d.%m.%Y").date())
        return upcoming


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError:
            return "Name not found."
        except ValueError as e:
            return f"Error: {e}"
        except IndexError:
            return "Not enough arguments."
        except KeyError:
            return "Name not found."
    return inner


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if not record.phones:
        return "No phones found."
    return "; ".join(p.value for p in record.phones)


def show_all(book: AddressBook):
    return str(book)


@input_error
def add_birthday(args, book: AddressBook):
    name, bday = args[0], args[1]
    record = book.find(name)
    record.add_birthday(bday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record.birthday is None:
        return "Birthday not set."
    return record.birthday.value


@input_error
def birthdays(args, book: AddressBook):
    days = int(args[0]) if args else 7
    upcoming = book.get_upcoming_birthdays(days=days)
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(f"{x['name']}: {x['congratulation_date']}" for x in upcoming)


def parse_input(user_input: str):
    user_input = (user_input or "").strip()
    if not user_input:
        return None, []
    parts = user_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args

"""
створення об'єкту серіалізації і його розпакування для використування у main()
"""

def save_data(book: AddressBook, filename: str = ADDRESS_FILE):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename: str = ADDRESS_FILE):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()
    


def main():
    book = load_data() #замість стрворення об'єкту класу, як було раніше
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command is None:
            continue

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add_birthday":
            print(add_birthday(args, book))

        elif command == "show_birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")
            
    save_data(book)


if __name__ == "__main__":
    main()
