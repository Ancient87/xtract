import flask_bcrypt
from app.main import db

class Financial(db.Model):
    __tablename__ = "financials"
    ticker = db.Column(db.String(10), primary_key=True)
    dividend_yield = db.Column(db.Float)
    beta = db.Column(db.Float)
    updated = db.Column(db.Date)
    company_name = db.Column(db.String(50))
    quote = db.Column(db.Float)

    def __repr__(self):
        return f"<ticker: {self.ticker}, yield: {self.dividend_yield}, beta:{self.beta}, updated:{self.updated}, {self.company_name}>"
        
    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class Ratio(db.Model):
    __tablename__ = "ratios"
    ticker = db.Column(db.String(10), db.ForeignKey("financials.ticker"), primary_key=True)
    period = db.Column(db.Date, primary_key=True)
    revenue = db.Column(db.Float)
    gross_margin = db.Column(db.Float)
    operating_income = db.Column(db.Float)
    operating_margin = db.Column(db.Float)
    net_income = db.Column(db.Float)
    eps = db.Column(db.Float)
    dividends = db.Column(db.Float)
    payout_ratio = db.Column(db.Float)
    shares = db.Column(db.Integer)
    bps = db.Column(db.Float)
    operating_cash_flow = db.Column(db.Float)
    cap_spending = db.Column(db.Float)
    fcf = db.Column(db.Float)
    working_capital = db.Column(db.Float)
    current_ratio = db.Column(db.Float)
    debt_equity = db.Column(db.Float)

    def __repr__(self):
        return "<ticker: {ticker}, period: {period}, eps: {eps}>".format(
            ticker=self.ticker, period=self.period, eps=self.eps
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class Valuation(db.Model):
    __tablename__ = "valuations"
    ticker = db.Column(db.String(10), db.ForeignKey("financials.ticker"), primary_key=True)
    year = db.Column(db.Date, primary_key=True)
    valuation = db.Column(db.Float)

    def __repr__(self):
        return "<ticker: {ticker}, valuation: {valuation}, year:{year}>".format(
            ticker=self.ticker, valuation=self.valuation, year=self.year
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])


class Dividend(db.Model):
    __tablename__ = "dividends"
    ticker = db.Column(db.String(10), db.ForeignKey("financials.ticker"), primary_key=True)
    period = db.Column(db.Date, primary_key=True)
    dividend = db.Column(db.Float)

    def __repr__(self):
        return "<ticker: {ticker}, period: {period}, dividend: {dividend}>".format(
            ticker=self.ticker, period=self.period, eps=self.dividend
        )

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])

