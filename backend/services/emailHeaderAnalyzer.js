const dns = require('dns').promises;

class EmailHeaderAnalyzer {
    static async analyze(emailContent) {
        const headers = this.parseHeaders(emailContent);
        const results = {
            score: 0,
            spf: 'unknown',
            dkim: 'unknown',
            dmarc: 'unknown',
            reply_to: 'unknown',
            anomalies: [],
            isSuspicious: false
        };

        const fromDomain = this.extractDomain(headers.from);
        if (!fromDomain) {
            results.anomalies.push('Invalid or missing "From" header');
            results.isSuspicious = true;
            return results;
        }

        await this.checkSPF(fromDomain, results);
        await this.checkDKIM(headers, fromDomain, results);
        await this.checkDMARC(fromDomain, results);
        this.checkReplyTo(headers, results);
        this.checkReturnPath(headers, results);

        results.score = this.calculateScore(results);
        results.isSuspicious = results.score < 60;

        return results;
    }

    static parseHeaders(email) {
        const headers = {};
        const lines = email.split('\n');
        for (const line of lines) {
            if (line.trim() === '') break;
            const match = line.match(/^([^:]+):\s*(.*)$/);
            if (match) {
                headers[match[1].toLowerCase()] = match[2].trim();
            }
        }
        return headers;
    }

    static extractDomain(email) {
        if (!email) return null;
        const match = email.match(/@([^\s>]+)/);
        return match ? match[1].toLowerCase() : null;
    }

    static async checkSPF(domain, results) {
        try {
            const records = await dns.resolveTxt(domain);
            const hasSPF = records.some(r => r.some(s => s.includes('v=spf1')));
            results.spf = hasSPF ? 'pass' : 'fail';
            if (!hasSPF) results.anomalies.push(`No SPF record for ${domain}`);
        } catch {
            results.spf = 'error';
        }
    }

    static async checkDKIM(headers, domain, results) {
        const dkimHeader = headers['dkim-signature'];
        if (!dkimHeader) {
            results.dkim = 'missing';
            results.anomalies.push('No DKIM signature');
            return;
        }

        try {
            const dkimParts = dkimHeader.split(';').reduce((acc, part) => {
                const [key, value] = part.trim().split('=');
                if (key && value) acc[key.trim()] = value.trim();
                return acc;
            }, {});

            if (dkimParts.d && dkimParts.d.toLowerCase() === domain) {
                const selector = dkimParts.s || 'default';
                const dkimDomain = `${selector}._domainkey.${domain}`;
                const records = await dns.resolveTxt(dkimDomain);
                results.dkim = records.length > 0 ? 'pass' : 'fail';
                if (records.length === 0) results.anomalies.push('DKIM record not found');
            } else {
                results.dkim = 'fail';
                results.anomalies.push('DKIM domain mismatch');
            }
        } catch {
            results.dkim = 'error';
        }
    }

    static async checkDMARC(domain, results) {
        try {
            const records = await dns.resolveTxt(`_dmarc.${domain}`);
            const hasDMARC = records.some(r => r.some(s => s.includes('v=DMARC1')));
            results.dmarc = hasDMARC ? 'pass' : 'fail';
            if (!hasDMARC) results.anomalies.push(`No DMARC record for ${domain}`);
        } catch {
            results.dmarc = 'error';
        }
    }

    static checkReplyTo(headers, results) {
        const replyTo = headers['reply-to'];
        const from = headers['from'];
        if (!replyTo) {
            results.reply_to = 'missing';
            results.anomalies.push('No Reply-To header');
            return;
        }

        const replyDomain = this.extractDomain(replyTo);
        const fromDomain = this.extractDomain(from);
        
        if (replyDomain && fromDomain && replyDomain !== fromDomain) {
            results.reply_to = 'suspicious';
            results.anomalies.push(`Reply-To domain (${replyDomain}) differs from From (${fromDomain})`);
        } else {
            results.reply_to = 'pass';
        }
    }

    static checkReturnPath(headers, results) {
        const returnPath = headers['return-path'];
        const from = headers['from'];
        if (!returnPath) {
            results.return_path = 'missing';
            return;
        }

        const returnDomain = this.extractDomain(returnPath);
        const fromDomain = this.extractDomain(from);
        
        if (returnDomain && fromDomain && returnDomain !== fromDomain) {
            results.return_path = 'suspicious';
            results.anomalies.push(`Return-Path domain (${returnDomain}) differs from From`);
        } else {
            results.return_path = 'pass';
        }
    }

    static calculateScore(results) {
        const checks = {
            spf: { pass: 100, fail: 0, error: 50, unknown: 50 },
            dkim: { pass: 100, fail: 0, missing: 0, error: 50, unknown: 50 },
            dmarc: { pass: 100, fail: 0, error: 50, unknown: 50 },
            reply_to: { pass: 100, suspicious: 0, missing: 50, unknown: 50 },
            return_path: { pass: 100, suspicious: 25, missing: 50, unknown: 50 }
        };

        let total = 0;
        let count = 0;
        const keys = ['spf', 'dkim', 'dmarc', 'reply_to', 'return_path'];

        for (const key of keys) {
            if (results[key] !== undefined) {
                total += (checks[key]?.[results[key]] || 50);
                count++;
            }
        }

        return count > 0 ? Math.round(total / count) : 0;
    }
}

module.exports = EmailHeaderAnalyzer;